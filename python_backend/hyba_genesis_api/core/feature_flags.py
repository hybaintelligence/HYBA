"""Runtime feature flags for public HYBA product surfaces."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any

from fastapi import HTTPException

DEFAULT_FLAGS = {
    "qaas_enabled": True,
    "qiaas_enabled": True,
    "finance_enabled": True,
    "developer_platform_enabled": True,
}


@lru_cache(maxsize=1)
def get_feature_flags() -> dict[str, bool]:
    raw = os.getenv("HYBA_FEATURE_FLAGS", "").strip()
    flags = dict(DEFAULT_FLAGS)
    if raw:
        parsed: Any = json.loads(raw)
        if not isinstance(parsed, dict):
            raise ValueError("HYBA_FEATURE_FLAGS must be a JSON object")
        for key, value in parsed.items():
            if key in flags:
                flags[key] = bool(value)
    return flags


def require_feature(flag_name: str) -> None:
    if not get_feature_flags().get(flag_name, False):
        raise HTTPException(status_code=503, detail=f"feature disabled: {flag_name}")
