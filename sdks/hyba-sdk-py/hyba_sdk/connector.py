"""
HYBA SDK Connector Configuration
Connector configuration for data sources
"""

from typing import Dict, Any, Optional, List
from enum import Enum


class ConnectorType(str, Enum):
    """Supported connector types"""
    SQL_POSTGRESQL = "sql_postgresql"
    SQL_MYSQL = "sql_mysql"
    SQL_SNOWFLAKE = "sql_snowflake"
    SQL_BIGQUERY = "sql_bigquery"
    KAFKA = "kafka"
    KINESIS = "kinesis"
    EVENT_HUB = "eventhub"
    S3 = "s3"
    AZURE_BLOB = "azure_blob"
    GCS = "gcs"
    HTTP = "http"
    REST_API = "rest_api"
    FILE = "file"
    SCADA = "scada"
    PUB_CHEM = "pubchem"
    PROTEIN = "protein"
    CLINICAL_TRIALS = "clinical_trials"
    LIMS = "lims"
    EHR = "ehr"
    IOT = "iot"
    CRM = "crm"
    HR = "hr"
    SCM = "scm"


class ConnectorConfig:
    """
    Configuration for data source connectors
    
    Example:
        >>> connector = ConnectorConfig(
        ...     type=ConnectorType.SQL_SNOWFLAKE,
        ...     host="acme.snowflakecomputing.com",
        ...     database="finance_dw",
        ...     query="SELECT * FROM positions"
        ... )
    """
    
    def __init__(
        self,
        type: ConnectorType,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        query: Optional[str] = None,
        table: Optional[str] = None,
        bucket: Optional[str] = None,
        key: Optional[str] = None,
        format: Optional[str] = None,
        broker: Optional[str] = None,
        topic: Optional[str] = None,
        endpoint: Optional[str] = None,
        path: Optional[str] = None,
        protocol: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize connector configuration
        
        Args:
            type: Connector type (from ConnectorType enum)
            host: Database/server host
            port: Port number
            database: Database name
            username: Username for authentication
            password: Password for authentication
            query: SQL query or API query
            table: Table name (alternative to query)
            bucket: S3/cloud storage bucket
            key: Object key/path
            format: File format (csv, parquet, json)
            broker: Kafka broker address
            topic: Kafka topic/stream name
            endpoint: HTTP endpoint URL
            path: File path
            protocol: Protocol (opcua, modbus, fix, etc.)
            config: Additional configuration dictionary
        """
        self.type = type
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.query = query
        self.table = table
        self.bucket = bucket
        self.key = key
        self.format = format
        self.broker = broker
        self.topic = topic
        self.endpoint = endpoint
        self.path = path
        self.protocol = protocol
        self.config = config or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for API request
        
        Returns:
            Dictionary representation
        """
        result = {"type": self.type.value}
        
        # Add non-None values
        optional_fields = [
            "host", "port", "database", "username", "password",
            "query", "table", "bucket", "key", "format",
            "broker", "topic", "endpoint", "path", "protocol", "config"
        ]
        
        for field in optional_fields:
            value = getattr(self, field)
            if value is not None:
                result[field] = value
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConnectorConfig":
        """
        Create from dictionary
        
        Args:
            data: Dictionary with connector configuration
            
        Returns:
            ConnectorConfig instance
        """
        # Convert type string to enum
        type_str = data.pop("type", "http")
        try:
            connector_type = ConnectorType(type_str)
        except ValueError:
            connector_type = ConnectorType.HTTP
        
        return cls(type=connector_type, **data)
    
    def __repr__(self) -> str:
        return f"ConnectorConfig(type={self.type.value}, host={self.host})"


class OutputConnectorConfig:
    """
    Configuration for output connectors (egress)
    
    Example:
        >>> output = OutputConnectorConfig(
        ...     type=OutputConnectorType.S3,
        ...     bucket="my-results",
        ...     format="parquet"
        ... )
    """
    
    def __init__(
        self,
        type: str,
        bucket: Optional[str] = None,
        key: Optional[str] = None,
        format: Optional[str] = None,
        endpoint: Optional[str] = None,
        protocol: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.type = type
        self.bucket = bucket
        self.key = key
        self.format = format
        self.endpoint = endpoint
        self.protocol = protocol
        self.config = config or {}
    
    def to_dict(self) -> Dict[str, Any]:
        result = {"type": self.type}
        optional_fields = [
            "bucket", "key", "format", "endpoint", "protocol", "config"
        ]
        for field in optional_fields:
            value = getattr(self, field)
            if value is not None:
                result[field] = value
        return result
    
    def __repr__(self) -> str:
        return f"OutputConnectorConfig(type={self.type})"