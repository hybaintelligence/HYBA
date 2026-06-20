# CONNECTOR IMPLEMENTATION SPECIFICATION
## Universal Data Ingestion & Egress Architecture

---

## ARCHITECTURE: CONNECTORS AS FIRST-CLASS INFRASTRUCTURE

```
┌─────────────────────────────────────────────────────┐
│         CONNECTOR ABSTRACTION LAYER                  │
│  (Universal interface: ingest → normalize → tensor)  │
└─────────────────────────────────────────────────────┘
        ↓ Ingress Connectors       ↓ Egress Connectors
┌──────────────────┐          ┌──────────────────┐
│   Data Sources   │          │ Result Targets   │
│  SQL, Kafka,     │          │ FIX, APIs,       │
│  S3, APIs, SCADA │          │ Data Lakes,      │
│  Bloomberg, EHR  │          │ Dashboards       │
└──────────────────┘          └──────────────────┘
```

---

## BASE CONNECTOR INTERFACE

All connectors inherit from `UniversalConnector`:

```python
# pythia_connectors/base.py

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Iterator
import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class DataType(Enum):
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    TEMPORAL = "temporal"
    SPATIAL = "spatial"
    TEXT = "text"

@dataclass
class ConnectorSchema:
    """Auto-detected schema from data source"""
    columns: Dict[str, DataType]
    row_count: int
    estimated_size_bytes: int
    last_updated: str
    sample_rows: pd.DataFrame
    missing_value_rate: float

@dataclass
class NormalizationConfig:
    """Auto-configuration for normalization"""
    scaling_method: str = "standardize"  # standardize, normalize, robust, log
    missing_value_method: str = "forward_fill"  # forward_fill, interpolate, drop
    categorical_encoding: str = "one_hot"  # one_hot, label, embedding
    temporal_resolution: str = "auto"  # auto, 1s, 1m, 1h, 1d
    feature_engineering: bool = True  # auto-generate interactions, ratios

class UniversalConnector(ABC):
    """
    Universal connector interface.
    All connectors (SQL, Kafka, S3, APIs, SCADA, etc.) implement this.
    """
    
    def __init__(self, config: Dict[str, Any], name: str = None):
        self.config = config
        self.name = name or self.__class__.__name__
        self.schema: Optional[ConnectorSchema] = None
        self._connection = None
        logger.info(f"Initializing connector: {self.name}")
    
    @abstractmethod
    def connect(self):
        """Establish connection to data source"""
        pass
    
    @abstractmethod
    def auto_detect_schema(self) -> ConnectorSchema:
        """
        Auto-detect data source schema.
        Returns column names, types, sample rows.
        """
        pass
    
    @abstractmethod
    def fetch_data(self, query: Optional[str] = None, limit: int = None) -> pd.DataFrame:
        """
        Fetch data from source.
        Returns: pandas DataFrame (rows=samples, cols=features)
        """
        pass
    
    @abstractmethod
    def stream_data(self, batch_size: int = 1000) -> Iterator[pd.DataFrame]:
        """
        Stream data in batches for real-time processing.
        Yields: batches of DataFrames
        """
        pass
    
    def normalize_data(self, df: pd.DataFrame, config: NormalizationConfig = None) -> np.ndarray:
        """
        Normalize data to matrix format suitable for HYBA tensor operations.
        
        Pipeline:
        1. Handle missing values
        2. Encode categorical variables
        3. Scale numerical features
        4. Generate temporal features (if applicable)
        5. Return as numpy array (float32)
        """
        if config is None:
            config = NormalizationConfig()
        
        df = df.copy()
        
        # Step 1: Handle missing values
        if config.missing_value_method == "forward_fill":
            df = df.fillna(method='ffill').fillna(method='bfill')
        elif config.missing_value_method == "interpolate":
            df = df.interpolate(method='linear')
        elif config.missing_value_method == "drop":
            df = df.dropna()
        
        # Step 2: Encode categoricals
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        if config.categorical_encoding == "one_hot":
            df = pd.get_dummies(df, columns=categorical_cols, drop_first=False)
        elif config.categorical_encoding == "label":
            from sklearn.preprocessing import LabelEncoder
            for col in categorical_cols:
                df[col] = LabelEncoder().fit_transform(df[col])
        
        # Step 3: Scale numerical features
        numerical_cols = df.select_dtypes(include=[np.number]).columns
        if config.scaling_method == "standardize":
            df[numerical_cols] = (df[numerical_cols] - df[numerical_cols].mean()) / df[numerical_cols].std()
        elif config.scaling_method == "normalize":
            df[numerical_cols] = (df[numerical_cols] - df[numerical_cols].min()) / (df[numerical_cols].max() - df[numerical_cols].min())
        elif config.scaling_method == "robust":
            from sklearn.preprocessing import RobustScaler
            df[numerical_cols] = RobustScaler().fit_transform(df[numerical_cols])
        
        # Step 4: Generate features
        if config.feature_engineering:
            # Auto-generate ratios for numerical columns
            if len(numerical_cols) >= 2:
                for i in range(len(numerical_cols) - 1):
                    for j in range(i + 1, len(numerical_cols)):
                        col1, col2 = numerical_cols[i], numerical_cols[j]
                        ratio_col = f"{col1}_over_{col2}"
                        df[ratio_col] = df[col1] / (df[col2] + 1e-8)
        
        # Step 5: Convert to numpy array
        return df.values.astype(np.float32)
    
    def compress_with_pulvini(self, data: np.ndarray, compression_target: float = 0.5):
        """
        Apply PULVINI φ-folding compression to data.
        Returns: (compressed_data, fold_depth, compression_ratio)
        """
        from pythia_mining.pulvini import PHIFoldingCompressor
        
        compressor = PHIFoldingCompressor(compression_target=compression_target)
        compressed = compressor.compress(data)
        
        return {
            'compressed': compressed,
            'fold_depth': compressor.fold_depth,
            'ratio': compressor.compression_ratio,
            'error_bound': compressor.error_bound
        }
    
    def ingest_and_normalize(self, query: str = None, compression: bool = True) -> Dict[str, Any]:
        """
        End-to-end ingestion pipeline.
        
        Returns:
        {
            'data': normalized numpy array,
            'schema': ConnectorSchema,
            'shape': (n_samples, n_features),
            'compression': {'ratio': 2.3, 'fold_depth': 5, ...}
        }
        """
        logger.info(f"Starting ingestion pipeline for {self.name}")
        
        # 1. Connect
        self.connect()
        
        # 2. Auto-detect schema
        self.schema = self.auto_detect_schema()
        logger.info(f"Detected schema: {self.schema.columns.keys()}")
        
        # 3. Fetch data
        df = self.fetch_data(query=query)
        logger.info(f"Fetched {len(df)} rows, {len(df.columns)} columns")
        
        # 4. Normalize
        normalized = self.normalize_data(df)
        logger.info(f"Normalized to shape {normalized.shape}")
        
        # 5. Compress (optional)
        compression_info = None
        if compression:
            compression_info = self.compress_with_pulvini(normalized)
            logger.info(f"PULVINI compression: {compression_info['ratio']:.2f}x")
        
        return {
            'data': normalized,
            'schema': self.schema,
            'shape': normalized.shape,
            'compression': compression_info
        }
    
    def disconnect(self):
        """Clean up connection"""
        if self._connection:
            self._connection.close()
            logger.info(f"Disconnected from {self.name}")

```

---

## CONNECTOR IMPLEMENTATIONS: PRIORITY LIST

### Tier 1 (Must-Have, Weeks 1-4)

#### 1. SQL Connector (`connector_sql.py`)
```python
class SQLConnector(UniversalConnector):
    """
    Universal SQL connector.
    Supports: PostgreSQL, MySQL, Oracle, SQL Server, Snowflake, BigQuery
    """
    
    DRIVERS = {
        'postgresql': 'psycopg2',
        'mysql': 'mysql-connector-python',
        'oracle': 'cx_Oracle',
        'snowflake': 'snowflake-connector-python',
        'bigquery': 'google-cloud-bigquery',
        'sqlserver': 'pyodbc'
    }
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.db_type = config.get('db_type', 'postgresql')
        self.connection_string = self._build_connection_string()
    
    def _build_connection_string(self) -> str:
        """Build connection string from config"""
        # Implementation for each DB type
        pass
    
    def connect(self):
        import sqlalchemy
        self._connection = sqlalchemy.create_engine(self.connection_string)
    
    def auto_detect_schema(self) -> ConnectorSchema:
        """Use sqlalchemy to inspect table schema"""
        inspector = sqlalchemy.inspect(self._connection)
        # ... schema detection logic
        pass
    
    def fetch_data(self, query: str, limit: int = None) -> pd.DataFrame:
        if limit:
            query += f" LIMIT {limit}"
        return pd.read_sql(query, self._connection)
    
    def stream_data(self, query: str, batch_size: int = 1000) -> Iterator[pd.DataFrame]:
        """Stream data in chunks"""
        for i in range(0, 1000000, batch_size):  # Assume max 1M rows
            offset_query = query + f" OFFSET {i} LIMIT {batch_size}"
            df = self.fetch_data(offset_query)
            if df.empty:
                break
            yield df
```

#### 2. Kafka Connector (`connector_kafka.py`)
```python
class KafkaConnector(UniversalConnector):
    """Real-time data from Kafka/Kinesis/Event Hubs"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.broker = config['broker']
        self.topic = config['topic']
        self.schema_registry = config.get('schema_registry')
    
    def connect(self):
        from confluent_kafka import Consumer
        self.consumer = Consumer({
            'bootstrap.servers': self.broker,
            'group.id': self.config.get('group_id', 'hyba-ciaas')
        })
        self.consumer.subscribe([self.topic])
    
    def stream_data(self, batch_size: int = 100) -> Iterator[pd.DataFrame]:
        """Stream messages from Kafka"""
        batch = []
        while True:
            msg = self.consumer.poll(timeout=1.0)
            if msg is None:
                if batch:
                    yield pd.DataFrame(batch)
                    batch = []
                continue
            
            # Parse message (JSON, Avro, etc.)
            data = json.loads(msg.value())
            batch.append(data)
            
            if len(batch) >= batch_size:
                yield pd.DataFrame(batch)
                batch = []
```

#### 3. S3/Data Lake Connector (`connector_data_lake.py`)
```python
class S3Connector(UniversalConnector):
    """AWS S3, Azure ADLS, Google Cloud Storage"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.bucket = config['bucket']
        self.key = config['key']
        self.format = config.get('format', 'parquet')  # parquet, csv, json
    
    def connect(self):
        import boto3
        self.s3 = boto3.client('s3')
    
    def fetch_data(self, query: str = None, limit: int = None) -> pd.DataFrame:
        obj = self.s3.get_object(Bucket=self.bucket, Key=self.key)
        
        if self.format == 'parquet':
            return pd.read_parquet(obj['Body'])
        elif self.format == 'csv':
            return pd.read_csv(obj['Body'])
        elif self.format == 'json':
            return pd.read_json(obj['Body'])
```

#### 4. REST API Connector (`connector_http.py`)
```python
class HTTPConnector(UniversalConnector):
    """Generic REST/GraphQL API connector"""
    
    def fetch_data(self, query: str = None) -> pd.DataFrame:
        import requests
        headers = self.config.get('headers', {})
        
        response = requests.get(self.config['endpoint'], headers=headers)
        data = response.json()
        
        # Auto-flatten JSON to DataFrame
        if isinstance(data, list):
            return pd.DataFrame(data)
        elif isinstance(data, dict):
            # Handle paginated responses
            if 'results' in data:
                return pd.DataFrame(data['results'])
            elif 'data' in data:
                return pd.DataFrame(data['data'])
```

#### 5. File Connector (`connector_files.py`)
```python
class FileConnector(UniversalConnector):
    """Local files, FTP, SFTP"""
    
    def fetch_data(self, query: str = None) -> pd.DataFrame:
        filepath = self.config['path']
        
        if filepath.endswith('.csv'):
            return pd.read_csv(filepath)
        elif filepath.endswith('.xlsx'):
            return pd.read_excel(filepath)
        elif filepath.endswith('.parquet'):
            return pd.read_parquet(filepath)
        elif filepath.endswith('.json'):
            return pd.read_json(filepath)
```

---

### Tier 2 (Finance, Weeks 5-8)

#### Bloomberg Terminal Connector
```python
class BloombergConnector(UniversalConnector):
    """Bloomberg Terminal API (B-PIPE, PORT)"""
    
    def fetch_data(self, securities: List[str], fields: List[str]) -> pd.DataFrame:
        from xbbg import blp
        data = blp.bdh(securities, fields, start_date='2020-01-01')
        return data
```

#### Crypto Exchange Connector
```python
class CryptoConnector(UniversalConnector):
    """Binance, Coinbase, Kraken APIs"""
    
    def stream_data(self, symbols: List[str], batch_size: int = 100):
        import ccxt
        exchange = ccxt.binance()
        
        for symbol in symbols:
            orderbook = exchange.fetch_order_book(symbol)
            # ... normalize to tensor
```

---

### Tier 3 (Pharma, Weeks 9-12)

#### PubChem Connector
```python
class PubChemConnector(UniversalConnector):
    """Chemical structure database"""
    
    def fetch_data(self, query: str) -> pd.DataFrame:
        # Search PubChem, return molecular fingerprints
        import requests
        
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/text/{query}/cids/JSON"
        response = requests.get(url)
        cids = response.json()['IdentifierList']['CID']
        
        # Convert SMILES to fingerprints
        molecules = []
        for cid in cids:
            smiles = self._get_smiles(cid)
            fp = self._compute_fingerprint(smiles)
            molecules.append({'cid': cid, 'fingerprint': fp})
        
        return pd.DataFrame(molecules)
```

#### LIMS Connector
```python
class LIMSConnector(UniversalConnector):
    """Lab Information Management Systems"""
    
    def fetch_data(self, query: str) -> pd.DataFrame:
        # LabWare, SLIMS, etc. via REST API
        pass
```

#### Clinical Trials Connector
```python
class ClinicalTrialsConnector(UniversalConnector):
    """ClinicalTrials.gov, EUDRACT"""
    
    def fetch_data(self, query: str) -> pd.DataFrame:
        import requests
        
        url = "https://clinicaltrials.gov/api/query/full_studies"
        params = {
            'expr': query,
            'fmt': 'json',
            'pageSize': 100
        }
        
        response = requests.get(url, params=params)
        trials = response.json()['NStudiesReturned']
        
        # Normalize trial data to feature matrix
        pass
```

---

## OUTPUT CONNECTORS (EGRESS)

```python
class OutputConnector(ABC):
    """Base class for output/result connectors"""
    
    @abstractmethod
    def write_results(self, results: Dict[str, Any]):
        """Write optimization results to target system"""
        pass
    
    @abstractmethod
    def stream_results(self, results_iterator):
        """Stream results in real-time"""
        pass

class FIXOutputConnector(OutputConnector):
    """Write orders via FIX protocol"""
    
    def write_results(self, orders: List[Dict]):
        from simplefix import FixParser
        
        for order in orders:
            msg = self._build_fix_message(order)
            self.connection.send(msg)

class S3OutputConnector(OutputConnector):
    """Write results to S3"""
    
    def write_results(self, results: Dict):
        import boto3
        s3 = boto3.client('s3')
        
        s3.put_object(
            Bucket=self.config['bucket'],
            Key=self.config['key'],
            Body=json.dumps(results)
        )

class WebhookOutputConnector(OutputConnector):
    """Call customer webhook with results"""
    
    def write_results(self, results: Dict):
        import requests
        
        requests.post(self.config['webhook_url'], json=results)
```

---

## INSTANCE PROVISIONING CONTROLLER

```python
# pythia_ciaas/provisioning.py

class CIaaSInstanceProvisioner:
    """Provisions CIaaS instances with connectors"""
    
    def provision(self, config: Dict) -> str:
        """
        Provision a new CIaaS instance.
        
        Returns: instance_id
        """
        instance_id = self._generate_id()
        
        # 1. Create ingress connector
        ingress = self._create_connector(
            config['ingress_connector_type'],
            config['ingress_connector_config']
        )
        
        # 2. Create egress connector
        egress = self._create_connector(
            config['egress_connector_type'],
            config['egress_connector_config']
        )
        
        # 3. Auto-detect package
        package = self._auto_select_package(config)
        
        # 4. Provision Docker container
        container_id = self._provision_docker(
            package=package,
            ingress=ingress,
            egress=egress,
            instance_id=instance_id
        )
        
        # 5. Configure autonomous healing
        self._configure_autonomous_healing(instance_id)
        
        # 6. Store configuration
        self._save_instance_config(instance_id, config)
        
        logger.info(f"Provisioned instance {instance_id}")
        return instance_id
    
    def _create_connector(self, connector_type: str, config: Dict):
        """Factory for connectors"""
        connectors = {
            'sql': SQLConnector,
            'kafka': KafkaConnector,
            's3': S3Connector,
            'http': HTTPConnector,
            'file': FileConnector,
            'bloomberg': BloombergConnector,
            'pubchem': PubChemConnector,
            # ... more connectors
        }
        
        connector_class = connectors.get(connector_type)
        if not connector_class:
            raise ValueError(f"Unknown connector type: {connector_type}")
        
        return connector_class(config)
    
    def _auto_select_package(self, config: Dict) -> str:
        """
        Infer optimal package based on data characteristics.
        
        - Portfolio data → optimization-engine
        - Molecular data → drug-discovery
        - Time-series → autonomous-optimization
        - etc.
        """
        data_type = config.get('data_type', 'auto')
        
        if data_type == 'auto':
            # Sample data, infer type
            connector = self._create_connector(
                config['ingress_connector_type'],
                config['ingress_connector_config']
            )
            schema = connector.auto_detect_schema()
            data_type = self._infer_data_type(schema)
        
        package_mapping = {
            'portfolio': 'optimization-engine',
            'molecule': 'drug-discovery-accelerator',
            'timeseries': 'autonomous-optimization',
            'tabular': 'optimization-engine',
        }
        
        return package_mapping.get(data_type, 'optimization-engine')
```

---

## TESTING CONNECTORS

```python
# tests/test_connectors.py

def test_sql_connector():
    config = {
        'db_type': 'postgresql',
        'host': 'localhost',
        'database': 'test',
        'query': 'SELECT * FROM test_table'
    }
    
    connector = SQLConnector(config)
    result = connector.ingest_and_normalize()
    
    assert result['shape'][0] > 0
    assert 'compression' in result

def test_kafka_connector():
    config = {
        'broker': 'localhost:9092',
        'topic': 'test-topic'
    }
    
    connector = KafkaConnector(config)
    batches = list(connector.stream_data(batch_size=10))
    
    assert len(batches) > 0

def test_s3_connector():
    config = {
        'bucket': 'test-bucket',
        'key': 'test.parquet'
    }
    
    connector = S3Connector(config)
    df = connector.fetch_data()
    
    assert len(df) > 0

def test_connector_normalization():
    # Raw data
    df = pd.DataFrame({
        'price': [100, 110, 120],
        'volume': [1000, 1100, 1200],
        'category': ['A', 'B', 'A']
    })
    
    connector = UniversalConnector({})
    normalized = connector.normalize_data(df)
    
    # Verify standardization
    assert np.abs(normalized.mean()) < 0.01
    assert np.abs(normalized.std() - 1.0) < 0.1

def test_provisioning():
    config = {
        'ingress_connector_type': 'sql',
        'ingress_connector_config': {
            'db_type': 'postgresql',
            'host': 'localhost',
            'database': 'test'
        },
        'egress_connector_type': 's3',
        'egress_connector_config': {
            'bucket': 'results',
            'key': 'output.json'
        }
    }
    
    provisioner = CIaaSInstanceProvisioner()
    instance_id = provisioner.provision(config)
    
    assert instance_id.startswith('hyba-')
```

---

## SUMMARY: CONNECTOR FRAMEWORK

**By end of Phase 1 (Week 4)**:
- 5 core connectors (SQL, Kafka, S3, HTTP, File)
- Any tabular data → provisioned instance in 5 minutes
- Automatic normalization + PULVINI compression
- Instant results to customer

**By end of Phase 5 (Month 12)**:
- 50+ connectors across all sectors
- Enterprise data ingestion + result output
- Autonomous healing across all instances
- "AWS of computational intelligence" positioning

**Pricing**: Per-connector instance (£100/month) + per-GB ingested (£1-£5)

**Differentiation**: No other platform matches this breadth of connectors + autonomous optimization.
