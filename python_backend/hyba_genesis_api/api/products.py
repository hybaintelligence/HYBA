"""Products/catalog API endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=Dict[str, Any])
async def list_products():
    """Return an empty measured catalog until a real catalog datastore is connected."""
    return {
        "items": [],
        "count": 0,
        "source": "catalog_datastore_not_connected",
        "timestamp": datetime.utcnow().isoformat(),
    }
