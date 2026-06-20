"""
HYBA CIaaS Universal Connector Framework
Data source agnostic, sector agnostic infrastructure
"""

from .base_connector import UniversalConnector, ConnectorSchema, NormalizationConfig, DataType
from .sql_connector import SQLConnector
from .kafka_connector import KafkaConnector, S3Connector
from .http_connector import HTTPConnector
from .scada_connector import SCADAConnector
from .pubchem_connector import PubChemConnector
from .protein_connector import ProteinConnector

__all__ = [
    'UniversalConnector',
    'ConnectorSchema',
    'NormalizationConfig',
    'DataType',
    'SQLConnector',
    'KafkaConnector',
    'S3Connector',
    'HTTPConnector',
    'SCADAConnector',
    'PubChemConnector',
    'ProteinConnector',
]
