"""Seed catalog contract tests for the frontend product panel."""

from __future__ import annotations

import asyncio

from hyba_genesis_api.api.products import list_products, load_seed_products


def test_seed_products_are_available_for_frontend_catalog() -> None:
    products = load_seed_products()

    assert len(products) >= 3
    assert {product["id"] for product in products} >= {
        "prod-pulvini-evidence-console",
        "prod-stratum-v1-command-room",
        "prod-phi-memory-folding",
    }
    for product in products:
        assert product["name"]
        assert product["description"]
        assert product["category"]
        assert isinstance(product["difficultyScale"], (int, float))
        assert isinstance(product["qubitDimension"], int)


def test_products_endpoint_returns_frontend_array_contract() -> None:
    products = asyncio.run(list_products())

    assert isinstance(products, list)
    assert products == load_seed_products()
