"""Compatibility shim for the consolidated PULVINI phi folding primitive.

Historically this path was a probe placeholder.  Keep the module importable for
old patch scripts while routing all behavior to the production implementation.
"""

from __future__ import annotations

from pythia_mining.phi_config import PHI, PHI_INV
from pythia_mining.phi_folding import PhiFoldingOperator

PulviniOperator = PhiFoldingOperator

__all__ = ["PHI", "PHI_INV", "PhiFoldingOperator", "PulviniOperator"]
