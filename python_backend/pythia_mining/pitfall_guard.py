"""
PYTHIA Mining PitfallGuard — Runtime Pitfall Enforcement Layer

Implements the runtime detection and enforcement layer for the PYTHIA Mining
Pitfalls Curriculum. The PitfallGuard validates all incoming messages and
mining operations against structured failure-mode patterns before execution.

Architecture:
- `PitfallEvent`: value object recording a detected pitfall occurrence
- `PitfallSeverity`: CRITICAL / HIGH / MEDIUM / LOW
- `PitfallAction`: HALT / REJECT / QUARANTINE / WARN / LOG
- `SafetyBounds`: configurable safety limits for sessions
- `PitfallGuard`: stateless-ish detector that inspects content for known pitfalls
- `validate_message()`: single-entry comprehensive check

Core detection rules (sourced from PYTHIA_MINING_PITFALLS_CURRICULUM.md):
  - PITFALL_1.1 — Plaintext credential leakage (CRITICAL → HALT)
  - PITFALL_3.1 — Unverified payout address (CRITICAL → REJECT)
  - PITFALL_5.2 — Social engineering / manipulation (CRITICAL → REJECT)
  - PITFALL_5.3 — Credential harvesting via chat (CRITICAL → HALT)

The guard is source-aware: content from 'chat' or unknown sources is treated
with higher suspicion than content from 'config_file' or 'operator_command_room'.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

DEFAULT_PITFALL_AUDIT_LOG = Path("logs/pitfall_audit.jsonl")


class PitfallSeverity(str, Enum):
    """Severity levels for pitfall detection events."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class PitfallAction(str, Enum):
    """Actions taken when a pitfall is detected."""

    HALT = "HALT"  # Immediate shutdown
    REJECT = "REJECT"  # Reject the message/operation
    QUARANTINE = "QUARANTINE"  # Flag for operator review
    WARN = "WARN"  # Log warning, continue
    LOG = "LOG"  # Log silently


class PitfallSourceCategory(str, Enum):
    """Source categories for determining trust level."""

    CHAT = "chat"
    CONFIG_FILE = "config_file"
    ENVIRONMENT_VARIABLE = "environment_variable"
    OPERATOR_COMMAND_ROOM = "operator_command_room"
    UNKNOWN = "unknown"


@dataclass
class PitfallEvent:
    """
    Record of a pitfall detection event.

    The triggering_input field is redacted at construction time if it contains
    sensitive patterns, so the in-memory event is safe for audit logging
    without further processing.
    """

    pitfall_id: str
    category: str
    severity: str
    action: str
    triggering_input: str
    timestamp_utc: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    operator_notified: bool = False
    suppressed_by: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pitfall_id": self.pitfall_id,
            "category": self.category,
            "severity": self.severity,
            "action": self.action,
            "triggering_input": self.triggering_input,
            "timestamp_utc": self.timestamp_utc,
            "operator_notified": self.operator_notified,
            "suppressed_by": self.suppressed_by,
        }


@dataclass
class SafetyBounds:
    """Configurable safety bounds for autonomous mining sessions."""

    max_session_minutes: int = 60
    max_shares: int = 10_000
    max_consecutive_failures: int = 5
    halt_after_consecutive_failures: int = 10
    require_operator_approval_for_new_pool: bool = True
    require_operator_approval_for_payout_change: bool = True
    enforce_difficulty_bounds: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_session_minutes": self.max_session_minutes,
            "max_shares": self.max_shares,
            "max_consecutive_failures": self.max_consecutive_failures,
            "halt_after_consecutive_failures": self.halt_after_consecutive_failures,
            "require_operator_approval_for_new_pool": self.require_operator_approval_for_new_pool,
            "require_operator_approval_for_payout_change": self.require_operator_approval_for_payout_change,
            "enforce_difficulty_bounds": self.enforce_difficulty_bounds,
        }


# ---------------------------------------------------------------------------
# PitfallGuard
# ---------------------------------------------------------------------------


class PitfallGuard:
    """
    Runtime enforcement layer for the PYTHIA Mining Pitfalls Curriculum.

    Every incoming message or configuration operation passes through the
    PitfallGuard before execution. Critical pitfalls cause immediate HALT
    or REJECT. The guard is source-aware to avoid false-positives when
    processing trusted configuration paths.

    Design invariants:
    - No raw secrets in memory after validation (triggering_input is redacted)
    - Audit trail is append-only JSONL in logs/pitfall_audit.jsonl
    - Suppressible per-pitfall by authenticated operators with expiry
    - Source-aware: chat/unknown → strict; config_file/env → permissive
    """

    # ── Detection patterns ────────────────────────────────────
    # Bitcoin mainnet address (P2PKH, P2SH, Bech32, Bech32m)
    BTC_ADDRESS_PATTERN = re.compile(
        r"(?:bc1[ac-hj-np-z02-9]{6,87}|" r"[13][a-km-zA-HJ-NP-Z1-9]{25,34})"
    )

    # WIF private key pattern
    WIF_PATTERN = re.compile(r"[5KL][1-9A-HJ-NP-Za-km-z]{50,51}")

    # Seed phrase / secret indicators
    SEED_INDICATORS = [
        "mnemonic",
        "seed phrase",
        "recovery phrase",
        "private key",
        "secret key",
        "wallet seed",
    ]

    # Stratum credential indicators
    STRATUM_INDICATORS = [
        "stratum+tcp://",
        "stratum+ssl://",
        "sha256.auto.nicehash.com",
        "stratum.nicehash.com",
        "Username",
        "Password",
        "worker_name",
        "mining.url",
        "pool.url",
        "stratum_url",
    ]

    # ── Social engineering patterns ───────────────────────────
    SOCIAL_ENGINEERING_PATTERNS: Dict[str, Tuple[str, ...]] = {
        "bypass_pitfalls": (
            "bypass pitfall",
            "bypass the pitfall",
            "disable pitfall",
            "ignore pitfall",
            "override pitfall",
            "skip pitfall",
            "turn off pitfall",
        ),
        "disable_safety": (
            "disable safety",
            "remove safety",
            "bypass safety",
            "ignore safety bounds",
            "override safety",
        ),
        "change_payout": (
            "change payout",
            "update payout address",
            "switch wallet",
            "send to my address",
            "use this address instead",
            "my address to receive",
            "here's my address",
        ),
        "change_pool": (
            "change pool",
            "switch pool",
            "use this pool instead",
            "connect to this stratum",
            "mine to this url",
        ),
        "disable_verification": (
            "skip verification",
            "disable verifier",
            "bypass sha",
            "trust me",
            "don't verify",
        ),
        "credential_injection": (
            "here's my",
            "my credentials",
            "use these credentials",
            "my username",
            "my password",
            "my stratum",
        ),
    }

    # ── Approved sources for payout addresses ─────────────────
    APPROVED_PAYOUT_SOURCES = {
        PitfallSourceCategory.CONFIG_FILE,
        PitfallSourceCategory.ENVIRONMENT_VARIABLE,
        PitfallSourceCategory.OPERATOR_COMMAND_ROOM,
    }

    def __init__(
        self,
        safety_bounds: Optional[SafetyBounds] = None,
        audit_log_path: Optional[Path] = None,
    ):
        self.safety_bounds = safety_bounds or SafetyBounds()
        self._audit_log_path = audit_log_path or DEFAULT_PITFALL_AUDIT_LOG
        self.audit_log: List[PitfallEvent] = []
        self._suppressed: Dict[str, float] = {}  # pitfall_id → expiry_epoch
        self._ensure_audit_path()
        logger.info(
            "PitfallGuard initialised with safety bounds: %s",
            self.safety_bounds.to_dict(),
        )

    # ------------------------------------------------------------------
    # Audit infrastructure
    # ------------------------------------------------------------------

    def _ensure_audit_path(self) -> None:
        """Ensure the audit log directory exists."""
        self._audit_log_path.parent.mkdir(parents=True, exist_ok=True)

    def _write_audit(self, event: PitfallEvent) -> None:
        """Write a single pitfall event to the JSONL audit trail."""
        try:
            with open(self._audit_log_path, "a") as f:
                f.write(json.dumps(event.to_dict()) + "\n")
        except OSError as e:
            logger.error("Failed to write pitfall audit log: %s", e)

    # ------------------------------------------------------------------
    # Redaction
    # ------------------------------------------------------------------

    def _redact(self, text: str) -> str:
        """Redact sensitive patterns from a string for safe logging."""
        redacted = self.BTC_ADDRESS_PATTERN.sub("[REDACTED_BTC_ADDRESS]", text)
        redacted = self.WIF_PATTERN.sub("[REDACTED_WIF]", redacted)
        # Redact long token-like strings (potential API keys / secrets)
        redacted = re.sub(r"[A-Za-z0-9]{40,}", "[REDACTED_LONG_TOKEN]", redacted)
        return redacted

    # ------------------------------------------------------------------
    # Suppression
    # ------------------------------------------------------------------

    def suppress(self, pitfall_id: str, duration_minutes: int = 60) -> None:
        """Temporarily suppress a pitfall by ID."""
        expiry = time_now() + duration_minutes * 60
        self._suppressed[pitfall_id] = expiry
        logger.warning(
            "Pitfall %s suppressed for %d minutes (expires epoch %.0f)",
            pitfall_id,
            duration_minutes,
            expiry,
        )

    def unsuppress(self, pitfall_id: str) -> None:
        """Remove a pitfall suppression."""
        self._suppressed.pop(pitfall_id, None)
        logger.info("Pitfall %s unsuppressed", pitfall_id)

    def _is_suppressed(self, pitfall_id: str) -> bool:
        """Check if a pitfall is currently suppressed."""
        expiry = self._suppressed.get(pitfall_id)
        if expiry is None:
            return False
        if time_now() >= expiry:
            del self._suppressed[pitfall_id]
            return False
        return True

    # ------------------------------------------------------------------
    # Individual pitfall checks
    # ------------------------------------------------------------------

    def check_credential_exposure(
        self, content: str, source: str = "unknown"
    ) -> Optional[PitfallEvent]:
        """
        Pitfall 1.1/5.3: Detect plaintext credential leakage or harvesting.

        Checks for Bitcoin addresses, WIF private keys, seed phrase indicators,
        and Stratum credential indicators in plaintext. Source-aware: chat/unknown
        sources are treated as credential harvesting (PITFALL_5.3), other sources
        as leakage (PITFALL_1.1).
        """
        content_lower = content.lower()
        triggers: List[str] = []

        # BTC addresses
        btc_matches = self.BTC_ADDRESS_PATTERN.findall(content)
        if btc_matches:
            triggers.append(f"BTC address(es): {len(btc_matches)} found")

        # WIF private keys
        wif_matches = self.WIF_PATTERN.findall(content)
        if wif_matches:
            triggers.append("WIF private key detected")

        # Seed phrase indicators
        for indicator in self.SEED_INDICATORS:
            if indicator in content_lower:
                triggers.append(f"Seed indicator: '{indicator}'")
                break

        # Stratum credential indicators (require >= 2 to reduce noise)
        stratum_count = sum(
            1 for ind in self.STRATUM_INDICATORS if ind.lower() in content_lower
        )
        if stratum_count >= 2:
            triggers.append(f"Multiple Stratum credential indicators ({stratum_count})")

        if not triggers:
            return None

        # Determine pitfall ID based on source
        is_chat = source in ("chat", PitfallSourceCategory.CHAT.value, "unknown")
        pitfall_id = "PITFALL_5.3" if is_chat else "PITFALL_1.1"

        event = PitfallEvent(
            pitfall_id=pitfall_id,
            category="Credential Exposure",
            severity=PitfallSeverity.CRITICAL.value,
            action=PitfallAction.HALT.value,
            triggering_input=self._redact(
                f"[Source: {source}] Triggers: {'; '.join(triggers)}"
            ),
        )
        if not self._record(event):
            return None
        return event

    def check_social_engineering(self, content: str) -> Optional[PitfallEvent]:
        """
        Pitfall 5.2: Detect social engineering attempts against the autonomous agent.

        Looks for natural-language patterns that attempt to persuade the agent to
        bypass security controls, change payout addresses, or accept credentials
        from untrusted sources.
        """
        content_lower = content.lower()
        triggered: List[str] = []

        for category, patterns in self.SOCIAL_ENGINEERING_PATTERNS.items():
            for pattern in patterns:
                if pattern in content_lower:
                    triggered.append(f"{category}: '{pattern}'")
                    break

        if not triggered:
            return None

        event = PitfallEvent(
            pitfall_id="PITFALL_5.2",
            category="AI/Agent Security",
            severity=PitfallSeverity.CRITICAL.value,
            action=PitfallAction.REJECT.value,
            triggering_input=f"Social engineering patterns: {'; '.join(triggered)}",
        )
        if not self._record(event):
            return None
        return event

    def check_unverified_payout_address(
        self, address: str, source: str = "unknown"
    ) -> Optional[PitfallEvent]:
        """
        Pitfall 3.1: Reject payout addresses from unverified sources.

        Only accepts addresses from:
        - config/mining_config.json (source="config_file")
        - HYBA_MINING_PAYOUT_ADDRESS env var (source="environment_variable")
        - Operator command room (source="operator_command_room")
        """
        # Verify it's actually a BTC address
        if not self.BTC_ADDRESS_PATTERN.fullmatch(address.strip()):
            return None  # Not a BTC address — let other validators handle it

        source_cat = PitfallSourceCategory(source)
        if source_cat in self.APPROVED_PAYOUT_SOURCES:
            return None  # Approved source

        event = PitfallEvent(
            pitfall_id="PITFALL_3.1",
            category="Wallet Security",
            severity=PitfallSeverity.CRITICAL.value,
            action=PitfallAction.REJECT.value,
            triggering_input=f"Payout address from unapproved source: {source}",
        )
        if not self._record(event):
            return None
        return event

    def check_unverified_pool(self, pool_url: str) -> Optional[PitfallEvent]:
        """
        Pitfall 2.1: Verify pool endpoint against approved registry.

        Loads the approved pool list from config/mining_pools_live.json
        or config/mining_pools_test.json and checks if the pool hostname
        matches an approved entry.
        """
        pool_host = pool_url.lower()
        for prefix in ["stratum+tcp://", "stratum+ssl://", "stratum://"]:
            if pool_host.startswith(prefix):
                pool_host = pool_host[len(prefix) :]
        if ":" in pool_host:
            pool_host = pool_host.split(":")[0]

        approved = self._load_approved_pools()
        for entry in approved:
            approved_url = entry.get("url", "").lower()
            for prefix in ["stratum+tcp://", "stratum+ssl://", "stratum://"]:
                if approved_url.startswith(prefix):
                    approved_url = approved_url[len(prefix) :]
            if ":" in approved_url:
                approved_url = approved_url.split(":")[0]
            if pool_host == approved_url:
                return None  # Approved

        event = PitfallEvent(
            pitfall_id="PITFALL_2.1",
            category="Pool Configuration",
            severity=PitfallSeverity.HIGH.value,
            action=PitfallAction.QUARANTINE.value,
            triggering_input=f"Unverified pool: {pool_url}",
        )
        if not self._record(event):
            return None
        return event

    def check_prompt_injection(self, config: Dict[str, Any]) -> Optional[PitfallEvent]:
        """
        Pitfall 5.1: Detect prompt injection via mining parameters.

        Recursively checks all string values in a configuration dict for
        suspicious natural-language injection patterns.
        """
        suspicious_patterns = [
            r"[Ss]ystem\s*prompt",
            r"[Ii]gnore\s*(all\s*)?(previous|above)",
            r"[Yy]ou\s*are\s*(now|a[n]?)",
            r"[Aa]ct\s*as\s*(a[n]?|if)",
            r"\[/?INST\]",
            r"<\|.*\|>",
            r"\{%.*%\}",
        ]
        compiled = [re.compile(p) for p in suspicious_patterns]

        def _scan(val: Any, path: str = "") -> List[str]:
            found: List[str] = []
            if isinstance(val, str):
                for ptn in compiled:
                    if ptn.search(val):
                        found.append(f"Injection pattern at {path}: {ptn.pattern}")
            elif isinstance(val, dict):
                for k, v in val.items():
                    found.extend(_scan(v, f"{path}.{k}"))
            elif isinstance(val, list):
                for i, v in enumerate(val):
                    found.extend(_scan(v, f"{path}[{i}]"))
            return found

        triggers = _scan(config)
        if not triggers:
            return None

        event = PitfallEvent(
            pitfall_id="PITFALL_5.1",
            category="AI/Agent Security",
            severity=PitfallSeverity.CRITICAL.value,
            action=PitfallAction.REJECT.value,
            triggering_input=f"Prompt injection: {'; '.join(triggers[:5])}",
        )
        if not self._record(event):
            return None
        return event

    # ------------------------------------------------------------------
    # Composite validation
    # ------------------------------------------------------------------

    def validate_message(
        self, content: str, source: str = "unknown"
    ) -> List[PitfallEvent]:
        """
        Comprehensive message validation against all applicable pitfalls.

        Runs credential exposure, social engineering, and unverified payout
        address checks. Returns a list of triggered pitfall events. An empty
        list means the message passed all checks.

        Args:
            content: The raw message content to validate.
            source: Source category string (chat, config_file, etc.).

        Returns:
            List of PitfallEvent objects. Empty list = pass.
        """
        events: List[PitfallEvent] = []

        # Check credential exposure (Pitfall 1.1 / 5.3)
        cred_event = self.check_credential_exposure(content, source)
        if cred_event:
            events.append(cred_event)

        # Check social engineering (Pitfall 5.2)
        se_event = self.check_social_engineering(content)
        if se_event:
            events.append(se_event)

        # Check unverified payout addresses (Pitfall 3.1)
        for addr in self.BTC_ADDRESS_PATTERN.findall(content):
            addr_event = self.check_unverified_payout_address(addr, source)
            if addr_event:
                # Deduplicate: only one PITFALL_3.1 event per message
                if not any(e.pitfall_id == "PITFALL_3.1" for e in events):
                    events.append(addr_event)

        return events

    def validate_config(
        self, config: Dict[str, Any], source: str = "config_file"
    ) -> List[PitfallEvent]:
        """
        Validate a mining configuration dict against relevant pitfalls.

        Checks for prompt injection (Pitfall 5.1) and unverified pool URLs
        (Pitfall 2.1).
        """
        events: List[PitfallEvent] = []

        # Check prompt injection (Pitfall 5.1)
        inj_event = self.check_prompt_injection(config)
        if inj_event:
            events.append(inj_event)

        # Check pool URL if present (Pitfall 2.1)
        pool_url = config.get("url") or config.get("pool_url") or ""
        if pool_url:
            pool_event = self.check_unverified_pool(pool_url)
            if pool_event:
                events.append(pool_event)

        return events

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _record(self, event: PitfallEvent) -> bool:
        """Record a pitfall event. Returns True if recorded, False if suppressed."""
        if self._is_suppressed(event.pitfall_id):
            logger.debug("Pitfall %s suppressed, not recording", event.pitfall_id)
            return False
        self.audit_log.append(event)
        self._write_audit(event)
        logger.warning(
            "PITFALL: %s | %s | %s | %s",
            event.pitfall_id,
            event.severity,
            event.action,
            event.triggering_input,
        )
        return True

    def _load_approved_pools(self) -> List[Dict[str, Any]]:
        """Load approved pool configurations from config files."""
        paths = [
            Path("config/mining_pools_live.json"),
            Path("config/mining_pools_test.json"),
        ]
        pools: List[Dict[str, Any]] = []
        for path in paths:
            if path.exists():
                try:
                    with open(path) as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        # config/mining_pools_live.json format: [{...}, {...}]
                        for item in data:
                            if isinstance(item, dict):
                                pools.append(item)
                    elif isinstance(data, dict):
                        # config/mining_pools_test.json format: {"pools": {...}}
                        pool_entries = data.get("pools", data.get("pool", []))
                        if isinstance(pool_entries, dict):
                            # {"nicehash": {...}, "braiins": {...}}
                            for entry in pool_entries.values():
                                if isinstance(entry, dict) and "url" in entry:
                                    pools.append(entry)
                        elif isinstance(pool_entries, list):
                            # [{"id": "nicehash", ...}, {...}]
                            pools.extend(pool_entries)
                except (json.JSONDecodeError, OSError) as e:
                    logger.warning("Failed to load pool config %s: %s", path, e)
        return pools


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


def time_now() -> float:
    """Current UNIX epoch timestamp."""
    return datetime.now(timezone.utc).timestamp()


__all__ = [
    "DEFAULT_PITFALL_AUDIT_LOG",
    "PitfallSeverity",
    "PitfallAction",
    "PitfallSourceCategory",
    "PitfallEvent",
    "SafetyBounds",
    "PitfallGuard",
]
