"""Sovereign/on-premise deployment control plane for HYBA CIaaS.

This module is deliberately dependency-light. It provides a local policy,
usage, admin, audit, and evidence layer that works in cloud, private cloud,
on-premise, sovereign-site, and air-gapped deployments.

The runtime is designed to sit in front of central ingestion and other HYBA
service actions. It does not depend on any cloud account, SaaS telemetry, or
external policy server.
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple, Union

from .ingestion import (
    DataIngestionService,
    DataSourceSpec,
    IngestionEnvelope,
    create_default_ingestion_service,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


class DeploymentMode(str, Enum):
    """Supported HYBA deployment topologies."""

    CLOUD = "cloud"
    PRIVATE_CLOUD = "private_cloud"
    ON_PREMISE = "on_premise"
    SOVEREIGN_SITE = "sovereign_site"
    AIR_GAPPED = "air_gapped"


class ActionType(str, Enum):
    """Common action categories enforced by the control plane."""

    INGEST_DATA = "ingest_data"
    READ_DATA = "read_data"
    EXECUTE_WORKLOAD = "execute_workload"
    ADMIN_MUTATION = "admin_mutation"
    PRIVILEGED_ADMIN_MUTATION = "privileged_admin_mutation"
    EXPORT_AUDIT = "export_audit"
    CHANGE_POLICY = "change_policy"


_CLEARANCE_ORDER = {
    "public": 0,
    "unclassified": 1,
    "internal": 2,
    "confidential": 3,
    "restricted": 4,
    "secret": 5,
    "top_secret": 6,
}

_CLOUD_SOURCE_TYPES = {
    "s3",
    "gcs",
    "adls",
    "blob",
    "bigquery",
    "snowflake",
    "cloud_storage",
    "object_store",
    "data_lake",
}

_EXTERNAL_NETWORK_SOURCE_TYPES = {
    "http",
    "api",
    "rest",
    "graphql",
    "webhook",
    "kafka",
    "kinesis",
    "eventhub",
    "stream",
    "event_stream",
    "events",
    "pubchem",
    "protein",
    "uniprot",
}


@dataclass(frozen=True)
class PrincipalContext:
    """Authenticated actor presented to the sovereign control plane."""

    principal_id: str
    roles: Tuple[str, ...] = field(default_factory=tuple)
    tenant_id: Optional[str] = None
    organisation_id: Optional[str] = None
    clearance: str = "unclassified"
    attributes: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "PrincipalContext":
        roles = payload.get("roles", ())
        if isinstance(roles, str):
            roles = (roles,)
        return cls(
            principal_id=str(payload["principal_id"]),
            roles=tuple(str(role) for role in roles),
            tenant_id=payload.get("tenant_id"),
            organisation_id=payload.get("organisation_id"),
            clearance=str(payload.get("clearance", "unclassified")),
            attributes=dict(payload.get("attributes") or {}),
        )

    def has_any_role(self, allowed_roles: Iterable[str]) -> bool:
        return bool(set(self.roles).intersection(set(allowed_roles)))


@dataclass
class UsagePolicy:
    """Local quotas that can be enforced without cloud billing infrastructure."""

    max_ingestions_per_day: Optional[int] = None
    max_records_per_ingestion: Optional[int] = None
    max_records_per_day: Optional[int] = None
    max_workloads_per_day: Optional[int] = None
    max_privileged_admin_actions_per_day: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_ingestions_per_day": self.max_ingestions_per_day,
            "max_records_per_ingestion": self.max_records_per_ingestion,
            "max_records_per_day": self.max_records_per_day,
            "max_workloads_per_day": self.max_workloads_per_day,
            "max_privileged_admin_actions_per_day": self.max_privileged_admin_actions_per_day,
        }


@dataclass
class SovereignDeploymentProfile:
    """Deployment profile for cloud, private-cloud, on-prem, sovereign, or air-gapped HYBA."""

    deployment_mode: DeploymentMode = DeploymentMode.CLOUD
    tenant_id: str = "default"
    jurisdiction: str = "global"
    site_name: Optional[str] = None
    data_residency: str = "global"
    classification_floor: str = "unclassified"
    allow_external_network: Optional[bool] = None
    allow_cloud_storage: Optional[bool] = None
    allowed_source_types: Optional[Tuple[str, ...]] = None
    restricted_operations: Tuple[str, ...] = field(default_factory=tuple)
    admin_roles: Tuple[str, ...] = ("admin", "security_admin", "sovereign_admin")
    auditor_roles: Tuple[str, ...] = ("admin", "auditor", "security_admin", "sovereign_admin")
    require_dual_control_for_privileged_admin: bool = True
    require_reason_for_privileged_admin: bool = True
    immutable_audit: bool = True
    usage_policy: UsagePolicy = field(default_factory=UsagePolicy)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.deployment_mode, str):
            self.deployment_mode = DeploymentMode(self.deployment_mode)

        if self.allow_external_network is None:
            self.allow_external_network = self.deployment_mode in {
                DeploymentMode.CLOUD,
                DeploymentMode.PRIVATE_CLOUD,
            }
        if self.allow_cloud_storage is None:
            self.allow_cloud_storage = self.deployment_mode in {
                DeploymentMode.CLOUD,
                DeploymentMode.PRIVATE_CLOUD,
            }

    @classmethod
    def from_environment(cls) -> "SovereignDeploymentProfile":
        """Create a deployment profile from HYBA_* environment variables."""

        def bool_env(name: str) -> Optional[bool]:
            if name not in os.environ:
                return None
            return os.environ[name].strip().lower() in {"1", "true", "yes", "on"}

        def csv_env(name: str) -> Tuple[str, ...]:
            raw = os.environ.get(name, "")
            return tuple(item.strip() for item in raw.split(",") if item.strip())

        dual_control_env = bool_env("HYBA_REQUIRE_DUAL_CONTROL_FOR_PRIVILEGED_ADMIN")
        reason_env = bool_env("HYBA_REQUIRE_REASON_FOR_PRIVILEGED_ADMIN")
        immutable_audit_env = bool_env("HYBA_IMMUTABLE_AUDIT")

        return cls(
            deployment_mode=DeploymentMode(os.environ.get("HYBA_DEPLOYMENT_MODE", "cloud")),
            tenant_id=os.environ.get("HYBA_TENANT_ID", "default"),
            jurisdiction=os.environ.get("HYBA_JURISDICTION", "global"),
            site_name=os.environ.get("HYBA_SITE_NAME"),
            data_residency=os.environ.get("HYBA_DATA_RESIDENCY", "global"),
            classification_floor=os.environ.get("HYBA_CLASSIFICATION_FLOOR", "unclassified"),
            allow_external_network=bool_env("HYBA_ALLOW_EXTERNAL_NETWORK"),
            allow_cloud_storage=bool_env("HYBA_ALLOW_CLOUD_STORAGE"),
            allowed_source_types=csv_env("HYBA_ALLOWED_SOURCE_TYPES") or None,
            restricted_operations=csv_env("HYBA_RESTRICTED_OPERATIONS"),
            admin_roles=csv_env("HYBA_ADMIN_ROLES") or ("admin", "security_admin", "sovereign_admin"),
            auditor_roles=csv_env("HYBA_AUDITOR_ROLES")
            or ("admin", "auditor", "security_admin", "sovereign_admin"),
            require_dual_control_for_privileged_admin=dual_control_env if dual_control_env is not None else True,
            require_reason_for_privileged_admin=reason_env if reason_env is not None else True,
            immutable_audit=immutable_audit_env if immutable_audit_env is not None else True,
            usage_policy=UsagePolicy(
                max_ingestions_per_day=_int_env("HYBA_MAX_INGESTIONS_PER_DAY"),
                max_records_per_ingestion=_int_env("HYBA_MAX_RECORDS_PER_INGESTION"),
                max_records_per_day=_int_env("HYBA_MAX_RECORDS_PER_DAY"),
                max_workloads_per_day=_int_env("HYBA_MAX_WORKLOADS_PER_DAY"),
                max_privileged_admin_actions_per_day=_int_env("HYBA_MAX_PRIVILEGED_ADMIN_ACTIONS_PER_DAY"),
            ),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "deployment_mode": self.deployment_mode.value,
            "tenant_id": self.tenant_id,
            "jurisdiction": self.jurisdiction,
            "site_name": self.site_name,
            "data_residency": self.data_residency,
            "classification_floor": self.classification_floor,
            "allow_external_network": self.allow_external_network,
            "allow_cloud_storage": self.allow_cloud_storage,
            "allowed_source_types": list(self.allowed_source_types or ()),
            "restricted_operations": list(self.restricted_operations),
            "admin_roles": list(self.admin_roles),
            "auditor_roles": list(self.auditor_roles),
            "require_dual_control_for_privileged_admin": self.require_dual_control_for_privileged_admin,
            "require_reason_for_privileged_admin": self.require_reason_for_privileged_admin,
            "immutable_audit": self.immutable_audit,
            "usage_policy": self.usage_policy.to_dict(),
            "metadata": dict(self.metadata),
        }


def _int_env(name: str) -> Optional[int]:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return None
    return int(raw)


@dataclass
class RestrictionDecision:
    """Decision returned by every control-plane evaluation."""

    allowed: bool
    action: str
    principal_id: str
    reasons: List[str] = field(default_factory=list)
    controls: Dict[str, Any] = field(default_factory=dict)
    evidence_seal: str = ""
    decided_at: str = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        if not self.evidence_seal:
            self.evidence_seal = _digest(
                {
                    "allowed": self.allowed,
                    "action": self.action,
                    "principal_id": self.principal_id,
                    "reasons": self.reasons,
                    "controls": self.controls,
                    "decided_at": self.decided_at,
                }
            )

    def assert_allowed(self) -> "RestrictionDecision":
        if not self.allowed:
            raise PermissionError("; ".join(self.reasons) or "HYBA control-plane policy denied the action")
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "action": self.action,
            "principal_id": self.principal_id,
            "reasons": list(self.reasons),
            "controls": dict(self.controls),
            "evidence_seal": self.evidence_seal,
            "decided_at": self.decided_at,
        }


@dataclass(frozen=True)
class AuditEvent:
    """Append-only audit event with hash-chain linkage."""

    event_id: str
    timestamp: str
    action: str
    principal_id: str
    tenant_id: Optional[str]
    allowed: bool
    reasons: Tuple[str, ...]
    metadata: Dict[str, Any]
    previous_hash: str
    evidence_seal: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "action": self.action,
            "principal_id": self.principal_id,
            "tenant_id": self.tenant_id,
            "allowed": self.allowed,
            "reasons": list(self.reasons),
            "metadata": dict(self.metadata),
            "previous_hash": self.previous_hash,
            "evidence_seal": self.evidence_seal,
        }


class SovereignControlPlane:
    """Local, auditable deployment and governance control plane for HYBA."""

    def __init__(self, profile: Optional[SovereignDeploymentProfile] = None) -> None:
        self.profile = profile or SovereignDeploymentProfile.from_environment()
        self._audit_log: List[AuditEvent] = []
        self._usage: Dict[Tuple[str, str, str], int] = {}

    def deployment_attestation(self) -> Dict[str, Any]:
        """Return machine-readable proof of the active deployment posture."""

        attestation = {
            "attested_at": _utc_now(),
            "profile": self.profile.to_dict(),
            "data_control_plane": "local" if self.is_local_sovereign_mode else "cloud_or_managed",
            "customer_data_leaves_site_by_default": False if self.is_local_sovereign_mode else None,
            "cloud_dependency_required": False if self.is_local_sovereign_mode else None,
            "audit_log_mode": "append_only_hash_chain" if self.profile.immutable_audit else "mutable",
            "enforcement_surfaces": [
                "deployment_mode",
                "data_residency",
                "network_egress",
                "cloud_storage",
                "admin_roles",
                "dual_control",
                "usage_quotas",
                "operation_restrictions",
                "clearance_classification",
            ],
        }
        attestation["evidence_seal"] = _digest(attestation)
        return attestation

    @property
    def is_local_sovereign_mode(self) -> bool:
        return self.profile.deployment_mode in {
            DeploymentMode.ON_PREMISE,
            DeploymentMode.SOVEREIGN_SITE,
            DeploymentMode.AIR_GAPPED,
        }

    def evaluate_action(
        self,
        principal: Union[PrincipalContext, Mapping[str, Any]],
        action: Union[ActionType, str],
        *,
        source: Optional[Union[DataSourceSpec, Mapping[str, Any]]] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        quantity: int = 1,
        record_audit: bool = True,
    ) -> RestrictionDecision:
        principal_ctx = principal if isinstance(principal, PrincipalContext) else PrincipalContext.from_mapping(principal)
        action_value = action.value if isinstance(action, ActionType) else str(action)
        meta = dict(metadata or {})
        reasons: List[str] = []
        controls = {
            "deployment_mode": self.profile.deployment_mode.value,
            "tenant_id": self.profile.tenant_id,
            "data_residency": self.profile.data_residency,
            "allow_external_network": self.profile.allow_external_network,
            "allow_cloud_storage": self.profile.allow_cloud_storage,
            "quantity": quantity,
        }

        if action_value in set(self.profile.restricted_operations):
            reasons.append(f"operation {action_value!r} is restricted by deployment profile")

        if action_value in {
            ActionType.ADMIN_MUTATION.value,
            ActionType.PRIVILEGED_ADMIN_MUTATION.value,
            ActionType.CHANGE_POLICY.value,
        } and not principal_ctx.has_any_role(self.profile.admin_roles):
            reasons.append("admin action requires an authorised admin role")

        if action_value == ActionType.PRIVILEGED_ADMIN_MUTATION.value:
            if self.profile.require_reason_for_privileged_admin and not meta.get("reason"):
                reasons.append("privileged admin action requires a reason")
            if self.profile.require_dual_control_for_privileged_admin and not (
                meta.get("second_approver") or meta.get("change_ticket")
            ):
                reasons.append("privileged admin action requires dual-control approval or a change ticket")
            if self._would_exceed_quota(
                principal_ctx,
                "privileged_admin_actions",
                quantity,
                self.profile.usage_policy.max_privileged_admin_actions_per_day,
            ):
                reasons.append("privileged admin daily quota exceeded")

        if action_value == ActionType.EXPORT_AUDIT.value and not principal_ctx.has_any_role(self.profile.auditor_roles):
            reasons.append("audit export requires an auditor/admin role")

        if source is not None:
            spec = source if isinstance(source, DataSourceSpec) else DataSourceSpec.from_mapping(source)
            controls.update(
                {
                    "source_type": spec.source_type,
                    "source_id": spec.canonical_source_id,
                    "source_sector": spec.sector,
                    "source_privacy_classification": spec.privacy_classification,
                    "source_data_residency": spec.metadata.get("data_residency"),
                }
            )
            self._evaluate_source_controls(principal_ctx, spec, reasons)

        if action_value == ActionType.INGEST_DATA.value:
            if self._would_exceed_quota(
                principal_ctx,
                "ingestions",
                1,
                self.profile.usage_policy.max_ingestions_per_day,
            ):
                reasons.append("daily ingestion quota exceeded")
            if self._would_exceed_quota(
                principal_ctx,
                "records",
                quantity,
                self.profile.usage_policy.max_records_per_day,
            ):
                reasons.append("daily record quota exceeded")
            if (
                self.profile.usage_policy.max_records_per_ingestion is not None
                and quantity > self.profile.usage_policy.max_records_per_ingestion
            ):
                reasons.append("records per ingestion exceed deployment usage policy")

        if action_value == ActionType.EXECUTE_WORKLOAD.value and self._would_exceed_quota(
            principal_ctx,
            "workloads",
            quantity,
            self.profile.usage_policy.max_workloads_per_day,
        ):
            reasons.append("daily workload quota exceeded")

        decision = RestrictionDecision(
            allowed=not reasons,
            action=action_value,
            principal_id=principal_ctx.principal_id,
            reasons=reasons,
            controls=controls,
        )
        if record_audit:
            self._append_audit_event(principal_ctx, decision, meta)
        return decision

    def authorize_ingestion(
        self,
        principal: Union[PrincipalContext, Mapping[str, Any]],
        source: Union[DataSourceSpec, Mapping[str, Any]],
        *,
        estimated_records: int = 1,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> RestrictionDecision:
        """Evaluate whether a data source may be ingested under this deployment profile."""

        return self.evaluate_action(
            principal,
            ActionType.INGEST_DATA,
            source=source,
            metadata=metadata,
            quantity=estimated_records,
        )

    def ingest_with_controls(
        self,
        principal: Union[PrincipalContext, Mapping[str, Any]],
        source: Union[DataSourceSpec, Mapping[str, Any]],
        *,
        service: Optional[DataIngestionService] = None,
        query: Optional[str] = None,
        limit: Optional[int] = None,
        estimated_records: int = 1,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> IngestionEnvelope:
        """Authorize, ingest, meter, and seal a central-ingestion run."""

        principal_ctx = principal if isinstance(principal, PrincipalContext) else PrincipalContext.from_mapping(principal)
        spec = source if isinstance(source, DataSourceSpec) else DataSourceSpec.from_mapping(source)
        decision = self.authorize_ingestion(
            principal_ctx,
            spec,
            estimated_records=estimated_records,
            metadata=metadata,
        )
        decision.assert_allowed()

        ingestion_service = service or create_default_ingestion_service()
        envelope = ingestion_service.ingest(spec, query=query, limit=limit)
        row_count = int(envelope.raw_shape[0])
        self.record_usage(principal_ctx, "ingestions", 1)
        self.record_usage(principal_ctx, "records", row_count)

        control_payload = {
            "decision": decision.to_dict(),
            "deployment_attestation": self.deployment_attestation(),
            "metered_records": row_count,
        }
        envelope.metadata["deployment_control"] = control_payload
        envelope.lineage.append(
            _lineage_event(
                "sovereign_controls_enforced",
                {
                    "deployment_mode": self.profile.deployment_mode.value,
                    "decision_evidence_seal": decision.evidence_seal,
                    "metered_records": row_count,
                },
            )
        )
        self._append_audit_event(
            principal_ctx,
            RestrictionDecision(
                allowed=True,
                action="ingestion_completed",
                principal_id=principal_ctx.principal_id,
                controls={
                    "run_id": envelope.run_id,
                    "source_id": envelope.source_id,
                    "row_count": row_count,
                    "deployment_mode": self.profile.deployment_mode.value,
                },
            ),
            metadata or {},
        )
        return envelope

    def record_usage(
        self,
        principal: Union[PrincipalContext, Mapping[str, Any]],
        usage_key: str,
        quantity: int = 1,
    ) -> int:
        principal_ctx = principal if isinstance(principal, PrincipalContext) else PrincipalContext.from_mapping(principal)
        key = (principal_ctx.principal_id, usage_key, date.today().isoformat())
        self._usage[key] = self._usage.get(key, 0) + int(quantity)
        return self._usage[key]

    def get_usage_snapshot(self, principal: Union[PrincipalContext, Mapping[str, Any]]) -> Dict[str, int]:
        principal_ctx = principal if isinstance(principal, PrincipalContext) else PrincipalContext.from_mapping(principal)
        today = date.today().isoformat()
        return {
            usage_key: value
            for (principal_id, usage_key, usage_date), value in self._usage.items()
            if principal_id == principal_ctx.principal_id and usage_date == today
        }

    def export_audit_log(
        self,
        principal: Union[PrincipalContext, Mapping[str, Any]],
        *,
        include_denied: bool = True,
    ) -> List[Dict[str, Any]]:
        decision = self.evaluate_action(
            principal,
            ActionType.EXPORT_AUDIT,
            metadata={"include_denied": include_denied},
            record_audit=True,
        )
        decision.assert_allowed()
        events = self._audit_log if include_denied else [event for event in self._audit_log if event.allowed]
        return [event.to_dict() for event in events]

    def _evaluate_source_controls(
        self,
        principal: PrincipalContext,
        spec: DataSourceSpec,
        reasons: List[str],
    ) -> None:
        source_type = spec.source_type.lower()
        allowed_types = {value.lower() for value in self.profile.allowed_source_types or ()}
        if allowed_types and source_type not in allowed_types:
            reasons.append(f"source type {spec.source_type!r} is not allowed by deployment profile")

        if source_type in _CLOUD_SOURCE_TYPES and not self.profile.allow_cloud_storage:
            reasons.append("cloud/object-storage ingestion is disabled for this deployment profile")

        if source_type in _EXTERNAL_NETWORK_SOURCE_TYPES and not self.profile.allow_external_network:
            reasons.append("external network ingestion is disabled for this deployment profile")

        source_residency = spec.metadata.get("data_residency")
        if source_residency and source_residency != self.profile.data_residency:
            reasons.append(
                f"source data residency {source_residency!r} does not match deployment residency {self.profile.data_residency!r}"
            )

        if _clearance_rank(principal.clearance) < _clearance_rank(spec.privacy_classification):
            reasons.append("principal clearance is below source privacy classification")

        if _clearance_rank(spec.privacy_classification) < _clearance_rank(self.profile.classification_floor):
            reasons.append("source classification is below deployment classification floor")

    def _would_exceed_quota(
        self,
        principal: PrincipalContext,
        usage_key: str,
        quantity: int,
        quota: Optional[int],
    ) -> bool:
        if quota is None:
            return False
        today = date.today().isoformat()
        current = self._usage.get((principal.principal_id, usage_key, today), 0)
        return current + int(quantity) > quota

    def _append_audit_event(
        self,
        principal: PrincipalContext,
        decision: RestrictionDecision,
        metadata: Mapping[str, Any],
    ) -> AuditEvent:
        previous_hash = self._audit_log[-1].evidence_seal if self._audit_log else "genesis"
        payload = {
            "timestamp": _utc_now(),
            "action": decision.action,
            "principal_id": principal.principal_id,
            "tenant_id": principal.tenant_id or self.profile.tenant_id,
            "allowed": decision.allowed,
            "reasons": decision.reasons,
            "decision_seal": decision.evidence_seal,
            "metadata": dict(metadata),
            "previous_hash": previous_hash,
        }
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=payload["timestamp"],
            action=decision.action,
            principal_id=principal.principal_id,
            tenant_id=principal.tenant_id or self.profile.tenant_id,
            allowed=decision.allowed,
            reasons=tuple(decision.reasons),
            metadata={
                "decision": decision.to_dict(),
                "request_metadata": dict(metadata),
                "profile_digest": _digest(self.profile.to_dict()),
            },
            previous_hash=previous_hash,
            evidence_seal=_digest(payload),
        )
        self._audit_log.append(event)
        return event


def _clearance_rank(value: str) -> int:
    return _CLEARANCE_ORDER.get(str(value).lower(), _CLEARANCE_ORDER["unclassified"])


def _lineage_event(step: str, details: Dict[str, Any]):
    from .ingestion import LineageEvent

    return LineageEvent(step=step, details=details)


def create_sovereign_control_plane(
    profile: Optional[SovereignDeploymentProfile] = None,
) -> SovereignControlPlane:
    """Factory used by HYBA services to create a local deployment control plane."""

    return SovereignControlPlane(profile=profile)
