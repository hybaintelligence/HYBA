"""Canonical-spelling import surface for the DIFC / AAOIFI Sukuk bridge.

The implementation currently lives in ``difc_aaiofi_bridge`` for backwards
compatibility with the first generated artifact name. New callers should import
this module because AAOIFI is the correct acronym spelling.
"""

from __future__ import annotations

from .difc_aaiofi_bridge import *  # noqa: F401,F403
