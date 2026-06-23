"""Runtime compatibility shims for HYBA backend startup.

These shims are intentionally narrow: they do not change autonomy policy or proposal
scoring. They only preserve backward compatibility for persisted proposal objects
whose confidence field predates the newer `counterfactual_confidence_score` name.
"""

from __future__ import annotations

import importlib.abc
import importlib.util
import sys
from types import ModuleType
from typing import Optional

_TARGET_MODULE = "pythia_mining.autonomous_mining_controller"


def _patch_pythia_proposal_confidence(module: ModuleType) -> None:
    proposal_cls = getattr(module, "SelfOptimizationProposal", None)
    if proposal_cls is None:
        return
    if hasattr(proposal_cls, "counterfactual_confidence_score"):
        return

    def _confidence_score(self: object) -> float:
        value = getattr(self, "counterfactual_confidence", 0.0)
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    setattr(proposal_cls, "counterfactual_confidence_score", property(_confidence_score))


class _PythiaCompatLoader(importlib.abc.Loader):
    def __init__(self, wrapped: importlib.abc.Loader) -> None:
        self._wrapped = wrapped

    def create_module(self, spec):  # type: ignore[no-untyped-def]
        create_module = getattr(self._wrapped, "create_module", None)
        if create_module is None:
            return None
        return create_module(spec)

    def exec_module(self, module: ModuleType) -> None:
        exec_module = getattr(self._wrapped, "exec_module")
        exec_module(module)
        _patch_pythia_proposal_confidence(module)


class _PythiaCompatFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname: str, path: Optional[list[str]], target=None):  # type: ignore[override]
        if fullname != _TARGET_MODULE:
            return None
        try:
            sys.meta_path.remove(self)
            spec = importlib.util.find_spec(fullname)
        finally:
            sys.meta_path.insert(0, self)
        if spec is None or spec.loader is None:
            return None
        spec.loader = _PythiaCompatLoader(spec.loader)
        return spec


def install_runtime_compatibility() -> None:
    """Install narrow runtime shims required for clean local demo startup."""
    existing = sys.modules.get(_TARGET_MODULE)
    if existing is not None:
        _patch_pythia_proposal_confidence(existing)
        return
    if any(isinstance(finder, _PythiaCompatFinder) for finder in sys.meta_path):
        return
    sys.meta_path.insert(0, _PythiaCompatFinder())
