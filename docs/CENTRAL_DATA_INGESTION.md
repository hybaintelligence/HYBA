# HYBA Central Data Ingestion System

## BLUF

HYBA now has a central, data-agnostic and sector-agnostic ingestion control plane.

The existing connector framework already knew how to speak to specific source classes such as SQL, event streams, HTTP APIs, object stores, SCADA, PubChem, and protein sources. The missing production layer was the shared service contract above those connectors. `hyba_ciaas.ingestion` now provides that layer.

## What this adds

```text
Any data source
  ↓
DataSourceSpec
  ↓
ConnectorRegistry
  ↓
DataIngestionService
  ↓
IngestionEnvelope
  ↓
HYBA services: optimisation, intelligence, mining, evidence, dashboards
```

The ingestion system treats sector as metadata, not as a code branch. That means finance, energy, biotech, government, industrial, retail, supply chain, scientific, and generic enterprise data all emit the same envelope.

## Core files

- `python_backend/hyba_ciaas/ingestion.py`
  - `DataSourceSpec`
  - `ConnectorRegistry`
  - `DataIngestionService`
  - `IngestionEnvelope`
  - `DataQualityReport`
  - `DataFrameConnector` fallback for inline records, arrays, JSON, CSV, text, and local files
- `tests/test_central_data_ingestion.py`
  - Validates the central ingestion envelope using finance, biotech, and energy examples without requiring live external systems.
- `python_backend/hyba_ciaas/__init__.py`
  - Exposes the ingestion service as a first-class package API.

## Supported source families

Default registry aliases include:

| Canonical type | Aliases |
|---|---|
| `inline` | `records`, `rows`, `dataframe`, `array` |
| `file` | `csv`, `json`, `jsonl`, `parquet`, `excel`, `text` |
| `sql` | `database`, `postgresql`, `mysql`, `oracle`, `snowflake`, `bigquery`, `sqlserver` |
| `stream` | `kafka`, `kinesis`, `eventhub`, `event_stream`, `events` |
| `object_store` | `s3`, `adls`, `gcs`, `data_lake`, `blob` |
| `http` | `api`, `rest`, `graphql`, `webhook` |
| `scada` | `industrial_iot`, `iot`, `opcua`, `modbus`, `energy` |
| `pubchem` | `chemistry`, `molecule`, `compound`, `drug_discovery` |
| `protein` | `fasta`, `pdb`, `uniprot`, `bioinformatics` |

## Service contract

Every ingestion produces an `IngestionEnvelope` containing:

- `run_id`
- `source_id`
- `source_type`
- `sector`
- connector name
- schema
- raw shape
- normalized matrix shape
- prepared data frame
- normalized numeric matrix
- quality report
- lineage events
- warnings
- privacy and purpose metadata
- optional compression metadata

This lets the rest of HYBA depend on one stable contract instead of importing sector-specific connectors directly.

## Example

```python
from hyba_ciaas.ingestion import DataSourceSpec, create_default_ingestion_service

service = create_default_ingestion_service()

envelope = service.ingest(
    DataSourceSpec(
        source_type="records",
        sector="financial_services",
        source_id="portfolio-risk-feed",
        tenant_id="acme-bank",
        purpose="risk optimisation",
        privacy_classification="confidential",
        config={
            "records": [
                {"asset": "AAPL", "weight": 0.35, "price": 187.42},
                {"asset": "NVDA", "weight": 0.25, "price": 143.18},
            ]
        },
    )
)

payload = envelope.to_service_payload()
```

## Production posture

This implementation does not claim that every named enterprise vendor integration is fully credentialed and live. It creates the central ingestion layer required to make those integrations cleanly productionisable:

1. connector registration lives in one registry;
2. source selection is explicit and auditable;
3. ingestion returns a common envelope;
4. lineage and data quality are mandatory;
5. arbitrary incoming data can be accepted through the fallback connector;
6. downstream services no longer need sector-specific ingestion code.

## Tests

Run:

```bash
pytest tests/test_central_data_ingestion.py -q
```

The tests are deliberately offline and deterministic. They validate the central contract without needing databases, cloud accounts, Kafka brokers, PubChem, SCADA simulators, or customer API credentials.
