"""
HYBA CIaaS Universal Connector Framework.

The base connector types are imported eagerly. Source-specific connectors are
loaded lazily so central ingestion can run offline without requiring every
optional enterprise/scientific dependency to be installed at import time.
"""

from .base_connector import (
    ConnectorSchema,
    DataType,
    NormalizationConfig,
    UniversalConnector,
)

_LAZY_CONNECTORS = {
    "SQLConnector": ".sql_connector",
    "KafkaConnector": ".kafka_connector",
    "S3Connector": ".kafka_connector",
    "HTTPConnector": ".http_connector",
    "SCADAConnector": ".scada_connector",
    "PubChemConnector": ".pubchem_connector",
    "ProteinConnector": ".protein_connector",
}


def __getattr__(name):
    if name not in _LAZY_CONNECTORS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from importlib import import_module

    module = import_module(_LAZY_CONNECTORS[name], package=__name__)
    connector = getattr(module, name)
    globals()[name] = connector
    return connector


__all__ = [
    "UniversalConnector",
    "ConnectorSchema",
    "NormalizationConfig",
    "DataType",
    "SQLConnector",
    "KafkaConnector",
    "S3Connector",
    "HTTPConnector",
    "SCADAConnector",
    "PubChemConnector",
    "ProteinConnector",
]
