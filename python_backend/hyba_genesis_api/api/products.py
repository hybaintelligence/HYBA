"""Products/catalog API endpoints backed by handover seed data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/products", tags=["products"])
ROOT = Path(__file__).resolve().parents[3]
SEED_CATALOG = ROOT / "config" / "frontend_seed_data.json"


def load_seed_products() -> List[Dict[str, Any]]:
    """Load deterministic frontend catalog records for handover demos."""
    try:
        payload = json.loads(SEED_CATALOG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=503, detail="frontend seed catalog unavailable") from exc
    products = payload.get("products")
    if not isinstance(products, list):
        raise HTTPException(status_code=503, detail="frontend seed catalog is malformed")
    return [dict(item) for item in products if isinstance(item, dict)]


@router.get("", response_model=List[Dict[str, Any]])
async def list_products() -> List[Dict[str, Any]]:
    """Return deterministic catalog records used to seed the frontend product panel."""
    return load_seed_products()
