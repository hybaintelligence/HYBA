"""
Tests for the central HYBA data ingestion system.

These tests intentionally use inline records so they validate the core service
contract without requiring customer databases, cloud credentials, Kafka brokers,
or sector-specific APIs.
"""

import numpy as np

from hyba_ciaas.ingestion import (
    ConnectorRegistry,
    DataFrameConnector,
    DataIngestionService,
    DataSourceSpec,
    create_default_ingestion_service,
)


def test_central_ingestion_records_are_sector_agnostic():
    service = create_default_ingestion_service()
    spec = DataSourceSpec(
        source_type="records",
        sector="financial_services",
        source_id="portfolio-risk-feed",
        tenant_id="acme-bank",
        purpose="risk optimisation",
        privacy_classification="confidential",
        tags=("finance", "portfolio", "risk"),
        config={
            "records": [
                {
                    "asset": "AAPL",
                    "weight": 0.35,
                    "price": 187.42,
                    "as_of": "2026-06-23T08:00:00Z",
                    "notes": "large cap technology exposure",
                },
                {
                    "asset": "NVDA",
                    "weight": 0.25,
                    "price": 143.18,
                    "as_of": "2026-06-23T08:00:00Z",
                    "notes": "accelerated compute exposure",
                },
            ]
        },
    )

    envelope = service.ingest(spec)

    assert envelope.source_id == "portfolio-risk-feed"
    assert envelope.sector == "financial_services"
    assert envelope.source_type == "inline"
    assert envelope.raw_shape == (2, 5)
    assert envelope.normalized_shape is not None
    assert envelope.normalized_shape[0] == 2
    assert envelope.normalized_data is not None
    assert envelope.normalized_data.dtype == np.float32
    assert envelope.quality.score > 0.8

    payload = envelope.to_service_payload()
    assert payload["metadata"]["tenant_id"] == "acme-bank"
    assert payload["metadata"]["privacy_classification"] == "confidential"
    assert "records" not in payload
    assert "normalized_data" not in payload


def test_central_ingestion_handles_nested_scientific_and_text_data():
    service = DataIngestionService(max_text_categories=2)
    spec = {
        "source_type": "json",
        "sector": "biotech",
        "source_id": "compound-screen",
        "config": {
            "data": [
                {
                    "compound_id": "CMPD-001",
                    "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O",
                    "assay": {"ic50_nm": 12.4, "target": "kinase"},
                    "vector": [0.1, 0.3, 0.8],
                    "free_text": "candidate molecule with strong kinase activity and clean assay signal",
                },
                {
                    "compound_id": "CMPD-002",
                    "smiles": "CCN(CC)CCOC(=O)C1=CC=CC=C1",
                    "assay": {"ic50_nm": 55.0, "target": "kinase"},
                    "vector": [0.2, 0.4, 0.5],
                    "free_text": "backup candidate with weaker binding but better developability notes",
                },
                {
                    "compound_id": "CMPD-003",
                    "smiles": "C1=CC=C(C=C1)C=O",
                    "assay": {"ic50_nm": 89.0, "target": "control"},
                    "vector": [0.8, 0.1, 0.2],
                    "free_text": "control molecule for negative class calibration",
                },
            ]
        },
    }

    envelope = service.ingest(spec)

    assert envelope.sector == "biotech"
    assert envelope.raw_shape[0] == 3
    assert envelope.normalized_shape is not None
    assert envelope.normalized_shape[0] == 3
    assert any(column.startswith("free_text__") for column in envelope.data.columns)
    assert any(
        "High-cardinality text column" in warning for warning in envelope.warnings
    )
    assert envelope.to_service_payload()["schema"]["columns"]["vector"] == "array"


def test_registry_resolves_existing_connector_aliases_and_fallbacks():
    registry = ConnectorRegistry.with_defaults()

    assert registry.resolve("postgresql") == "sql"
    assert registry.resolve("REST") == "http"
    assert registry.resolve("data-lake") == "object_store"
    assert registry.resolve("records") == "inline"

    connector = registry.create_connector(
        DataSourceSpec(
            source_type="records",
            config={"records": [{"x": 1}, {"x": 2}]},
        )
    )
    assert isinstance(connector, DataFrameConnector)


def test_streaming_envelopes_share_the_same_ingestion_contract():
    service = create_default_ingestion_service()
    spec = DataSourceSpec(
        source_type="records",
        sector="energy",
        source_id="grid-telemetry-inline",
        batch_size=2,
        config={
            "records": [
                {"node": "N1", "mw": 10.0, "frequency": 50.0},
                {"node": "N2", "mw": 11.0, "frequency": 50.1},
                {"node": "N3", "mw": 9.8, "frequency": 49.9},
            ]
        },
    )

    batches = list(service.stream(spec, max_batches=2))

    assert len(batches) == 2
    assert batches[0].source_id == "grid-telemetry-inline"
    assert batches[0].sector == "energy"
    assert batches[0].normalized_shape[0] == 2
    assert batches[1].normalized_shape[0] == 1
    assert batches[0].to_service_payload()["metadata"]["batch_index"] == 0
