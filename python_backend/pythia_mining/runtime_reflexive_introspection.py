"""Runtime reflexive introspection adapters for PYTHIA.

This module addresses two production-evidence gaps identified in the repo-grounded
review:

1. The boot-time reflexive surroundings must be derived from the live repository
   surface, not a fixed lookup table.
2. The virtual mining session used during startup should exercise a deterministic
   hash landscape, not only multiply proposal-quality factors.

The adapters are intentionally non-mutating: they do not edit source files, connect
to pools, or submit shares. They refresh the controller's in-memory surroundings
and replace the instance-level virtual simulation function during bootstrap.
"""

from __future__ import annotations

import ast
import hashlib
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

INVARIANT_HINTS: dict[str, str] = {
    "hermit": "density_matrix_self_adjoint",
    "psd": "density_matrix_nonnegative_eigenvalues",
    "positive_semidefinite": "density_matrix_nonnegative_eigenvalues",
    "phi": "golden_ratio_alignment",
    "golden": "golden_ratio_alignment",
    "yang_mills": "mass_gap_spectral_condition",
    "mass_gap": "mass_gap_spectral_condition",
    "compression": "lossless_compression_invertibility",
    "pulvini": "lossless_compression_invertibility",
    "firewall": "authority_separation_verification_boundary",
    "stratum": "pool_protocol_correctness",
    "bitcoin": "sha256d_header_validation",
    "audit": "explainability_traceability",
    "midas": "strict_state_machine_governance",
}

STABLE_CORE_HINTS = (
    "validation",
    "firewall",
    "certificate",
    "proof",
    "golden",
    "bitcoin",
    "midas_controls",
)


@dataclass(frozen=True)
class ModuleInspection:
    name: str
    path: str
    lines: int
    imports: tuple[str, ...]
    classes: int
    functions: int
    invariant_hits: tuple[str, ...]

    @property
    def entropy_score(self) -> float:
        return float(self.lines + 5 * self.functions + 8 * self.classes + 3 * len(self.imports))


def _module_name(root: Path, path: Path) -> str:
    rel = path.relative_to(root).with_suffix("")
    return ".".join(rel.parts)


def _safe_parse(path: Path) -> ast.AST | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return None


def _import_name(node: ast.AST, current_package: str) -> str | None:
    if isinstance(node, ast.Import):
        if not node.names:
            return None
        return node.names[0].name
    if isinstance(node, ast.ImportFrom):
        if node.module:
            return node.module
        if node.level > 0 and node.names:
            return f"{current_package}.{node.names[0].name}"
    return None


def inspect_python_modules(package_root: Path) -> list[ModuleInspection]:
    """Return AST-derived module inspections for a package tree."""

    modules: list[ModuleInspection] = []
    package_root = package_root.resolve()
    for path in sorted(package_root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        module = _safe_parse(path)
        text = path.read_text(encoding="utf-8", errors="replace")
        name = _module_name(package_root, path)
        imports: list[str] = []
        classes = 0
        functions = 0
        if module is not None:
            for node in ast.walk(module):
                if isinstance(node, ast.ClassDef):
                    classes += 1
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions += 1
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    imported = _import_name(node, package_root.name)
                    if imported:
                        imports.append(imported)
        haystack = f"{name}\n{text}".lower()
        invariant_hits = tuple(
            sorted({hint for hint in INVARIANT_HINTS if hint in haystack})
        )
        modules.append(
            ModuleInspection(
                name=name,
                path=str(path),
                lines=max(1, text.count("\n") + 1),
                imports=tuple(sorted(set(imports))),
                classes=classes,
                functions=functions,
                invariant_hits=invariant_hits,
            )
        )
    return modules


def _edge_weight(source: ModuleInspection, target: ModuleInspection) -> float:
    shared_invariants = set(source.invariant_hits).intersection(target.invariant_hits)
    import_affinity = 0.25 if target.name in source.imports or target.name.split(".")[-1] in source.imports else 0.0
    invariant_affinity = min(0.55, 0.11 * len(shared_invariants))
    entropy_balance = 1.0 - min(abs(source.entropy_score - target.entropy_score) / 2_000.0, 0.30)
    return round(max(0.10, min(0.99, 0.20 + import_affinity + invariant_affinity + 0.20 * entropy_balance)), 3)


def _build_edges(modules: list[ModuleInspection]) -> list[tuple[str, str, float]]:
    module_by_leaf = {module.name.split(".")[-1]: module for module in modules}
    module_by_name = {module.name: module for module in modules}
    edges: list[tuple[str, str, float]] = []
    seen: set[tuple[str, str]] = set()
    for module in modules:
        for imported in module.imports:
            candidate = module_by_name.get(imported) or module_by_leaf.get(imported.split(".")[-1])
            if not candidate or candidate.name == module.name:
                continue
            key = (module.name, candidate.name)
            if key in seen:
                continue
            seen.add(key)
            edges.append((module.name, candidate.name, _edge_weight(module, candidate)))
    if edges:
        return sorted(edges, key=lambda item: (-item[2], item[0], item[1]))[:256]

    # Fallback when imports are too dynamic: connect invariant-related modules.
    invariant_modules = [m for m in modules if m.invariant_hits]
    for left, right in zip(invariant_modules, invariant_modules[1:]):
        edges.append((left.name, right.name, _edge_weight(left, right)))
    return edges[:256]


def build_runtime_surroundings(controller: Any, package_root: Path | None = None) -> Any:
    """Build a CodebaseSurroundings instance using the controller's dataclass type."""

    if package_root is None:
        package_root = Path(__file__).resolve().parents[1] / "pythia_mining"
    inspections = inspect_python_modules(package_root)
    if not inspections:
        return controller._build_codebase_surroundings()

    module_names = [module.name for module in inspections]
    invariants: dict[str, str] = {}
    for module in inspections:
        for hit in module.invariant_hits:
            invariants[hit] = INVARIANT_HINTS[hit]
    invariants.setdefault("repository_introspection", "ast_import_graph_runtime_scan")

    entropy_sources = [
        module.name
        for module in sorted(inspections, key=lambda item: item.entropy_score, reverse=True)[:12]
    ]
    stable_core = [
        module.name
        for module in inspections
        if any(hint in module.name for hint in STABLE_CORE_HINTS) or module.invariant_hits
    ][:24]
    surroundings_type = type(controller.surroundings)
    return surroundings_type(
        module_names=module_names,
        mathematical_invariants=invariants,
        codebase_graph_edges=_build_edges(inspections),
        entropy_sources=entropy_sources,
        stable_core=stable_core,
    )


def refresh_controller_surroundings(controller: Any, package_root: Path | None = None) -> dict[str, Any]:
    """Refresh controller.surroundings from the live repository package tree."""

    previous_count = len(controller.surroundings.module_names)
    surroundings = build_runtime_surroundings(controller, package_root)
    controller.surroundings = surroundings
    return {
        "source": "runtime_ast_import_graph",
        "previous_module_count": previous_count,
        "module_count": len(surroundings.module_names),
        "edge_count": len(surroundings.codebase_graph_edges),
        "invariant_count": len(surroundings.mathematical_invariants),
        "entropy_source_count": len(surroundings.entropy_sources),
        "stable_core_count": len(surroundings.stable_core),
    }


def _normalise_hash_score(digest: bytes) -> float:
    value = int.from_bytes(digest, "big")
    return 1.0 - (value / float((1 << (8 * len(digest))) - 1))


def simulate_virtual_mining_with_hash_landscape(controller: Any, proposal: Any) -> float:
    """Deterministically score a proposal against an in-memory SHA-256d landscape.

    This is not pool-side evidence and does not claim mainnet revenue. It gives the
    reflexive loop a reproducible local mining-shaped landscape that reacts to
    proposal type, proposal value, constraint violations, confidence and logical
    consistency.
    """

    current_density = float(controller.get_phi_density())
    horizon = max(float(getattr(controller.config, "virtual_session_horizon", 0.25)), 0.01)
    samples = max(16, min(512, int(horizon * 512)))
    seed = json_seed = (
        f"{proposal.proposal_id}|{proposal.improvement_type}|{proposal.current_value:.12f}|"
        f"{proposal.proposed_value:.12f}|{proposal.logical_consistency_score:.12f}|"
        f"{proposal.counterfactual_confidence:.12f}"
    ).encode("utf-8")
    del json_seed

    scores: list[float] = []
    for nonce in range(samples):
        first = hashlib.sha256(seed + nonce.to_bytes(8, "big", signed=False)).digest()
        digest = hashlib.sha256(first).digest()
        scores.append(_normalise_hash_score(digest))

    best = max(scores)
    top_k = sorted(scores, reverse=True)[: max(1, int(math.sqrt(samples)))]
    top_mean = sum(top_k) / len(top_k)
    landscape_signal = 0.65 * best + 0.35 * top_mean

    violation_penalty = min(0.50, 0.10 * len(getattr(proposal, "constraints_violated", [])))
    consistency = max(0.0, min(1.0, float(proposal.logical_consistency_score)))
    confidence = max(0.0, min(1.0, float(proposal.counterfactual_confidence)))
    expected_gain = float(proposal.expected_phi_density_gain)
    quality = max(0.0, (1.0 - violation_penalty) * (0.55 * consistency + 0.45 * confidence))

    mining_delta = (landscape_signal - 0.50) * 0.04
    simulated_density = current_density + expected_gain * quality + mining_delta - violation_penalty * 0.05
    return min(max(simulated_density, 0.0), 1.0)


def bind_runtime_reflexive_adapters(controller: Any, package_root: Path | None = None) -> dict[str, Any]:
    """Refresh surroundings and bind deterministic virtual simulation at instance scope."""

    surroundings_report = refresh_controller_surroundings(controller, package_root)

    def _runtime_virtual_mining(proposal: Any) -> float:
        return simulate_virtual_mining_with_hash_landscape(controller, proposal)

    controller._simulate_virtual_mining = _runtime_virtual_mining  # noqa: SLF001
    return {
        **surroundings_report,
        "virtual_mining_simulation": "deterministic_sha256d_hash_landscape",
    }
