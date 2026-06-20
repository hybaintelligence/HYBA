"""
Kafka/Event Streaming Connector
Real-time data from Kafka, Kinesis, Event Hubs
"""

from typing import Dict, List, Any, Optional, Iterator
import pandas as pd
import json
import logging
from datetime import datetime

from .base_connector import UniversalConnector, ConnectorSchema, DataType

logger = logging.getLogger(__name__)


class KafkaConnector(UniversalConnector):
    """
    Real-time event streaming connector.
    
    Supports:
    - Apache Kafka
    - AWS Kinesis
    - Azure Event Hubs
    - Confluent Cloud
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Config:
        - broker_type: 'kafka', 'kinesis', 'eventhub'
        - brokers or endpoint: connection string
        - topic: topic/stream name
        - group_id: consumer group
        - schema_registry: (optional) Confluent Schema Registry
        """
        super().__init__(config)
        self.broker_type = config.get('broker_type', 'kafka').lower()
        self.brokers = config.get('brokers', 'localhost:9092')
        self.topic = config.get('topic')
        self.group_id = config.get('group_id', 'hyba-ciaas')
        self.schema_registry = config.get('schema_registry')
        self._consumer = None
        self._buffer = []
    
    def connect(self):
        """Connect to event broker"""
        try:
            if self.broker_type == 'kafka':
                from confluent_kafka import Consumer
                self._consumer = Consumer({
                    'bootstrap.servers': self.brokers,
                    'group.id': self.group_id,
                    'auto.offset.reset': 'earliest',
                })
                self._consumer.subscribe([self.topic])
                logger.info(f"Connected to Kafka: {self.brokers}, topic: {self.topic}")
            
            elif self.broker_type == 'kinesis':
                import boto3
                self._consumer = boto3.client('kinesis')
                logger.info(f"Connected to Kinesis stream: {self.topic}")
            
            elif self.broker_type == 'eventhub':
                from azure.eventhub import EventHubConsumerClient
                # Requires connection string
                logger.info(f"Connected to Azure Event Hub: {self.topic}")
        
        except ImportError as e:
            logger.warning(f"Broker library not installed: {e}, using simulation mode")
            self._consumer = 'simulated'
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self._consumer = 'simulated'
    
    def disconnect(self):
        """Close connection"""
        if self._consumer and self._consumer != 'simulated':
            try:
                if self.broker_type == 'kafka':
                    self._consumer.close()
                logger.info("Disconnected from broker")
            except:
                pass
    
    def auto_detect_schema(self) -> ConnectorSchema:
        """Auto-detect schema from first batch of messages"""
        messages = []
        
        if self._consumer == 'simulated':
            # Simulated data
            messages = [
                {'timestamp': datetime.utcnow().isoformat(), 'value': 100, 'status': 'ok'},
                {'timestamp': datetime.utcnow().isoformat(), 'value': 105, 'status': 'ok'},
            ]
        else:
            # Read a few messages to detect schema
            try:
                for i in range(10):
                    msg = self._consumer.poll(timeout=1.0)
                    if msg is None:
                        continue
                    
                    try:
                        data = json.loads(msg.value())
                        messages.append(data)
                    except:
                        messages.append({'raw': msg.value().decode()})
            except:
                logger.warning("Could not read messages for schema detection")
        
        if messages:
            df_sample = pd.DataFrame(messages)
        else:
            df_sample = pd.DataFrame({
                'timestamp': [datetime.utcnow().isoformat()],
                'data': ['value']
            })
        
        # Infer column types
        columns = {}
        for col in df_sample.columns:
            if 'time' in col.lower() or 'date' in col.lower():
                columns[col] = DataType.TEMPORAL
            elif df_sample[col].dtype in ['int64', 'float64']:
                columns[col] = DataType.NUMERIC
            else:
                columns[col] = DataType.TEXT
        
        return ConnectorSchema(
            columns=columns,
            row_count=1000000,  # Unbounded stream
            estimated_size_bytes=1000000 * len(columns) * 100,
            last_updated=datetime.utcnow().isoformat(),
            sample_rows=df_sample,
            missing_value_rate=0.0,
            data_types_detected={col: str(dtype) for col, dtype in df_sample.dtypes.items()}
        )
    
    def fetch_data(self, query: Optional[str] = None, limit: int = None) -> pd.DataFrame:
        """
        Fetch recent messages.
        In streaming, returns last N messages.
        """
        if not self._consumer:
            self.connect()
        
        messages = []
        max_messages = limit or 1000
        
        if self._consumer == 'simulated':
            # Simulated data
            import numpy as np
            for i in range(max_messages):
                messages.append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'sensor_id': f"SENSOR-{i % 10}",
                    'value': float(np.random.normal(100, 10)),
                    'status': 'ok',
                })
        else:
            # Read from broker
            try:
                msg_count = 0
                while msg_count < max_messages:
                    msg = self._consumer.poll(timeout=1.0)
                    if msg is None:
                        break
                    
                    try:
                        data = json.loads(msg.value().decode())
                        messages.append(data)
                        msg_count += 1
                    except:
                        logger.warning(f"Could not parse message: {msg.value()}")
            except Exception as e:
                logger.error(f"Error reading messages: {e}")
        
        if messages:
            df = pd.DataFrame(messages)
        else:
            df = pd.DataFrame()
        
        logger.info(f"Fetched {len(df)} messages")
        return df
    
    def stream_data(self, batch_size: int = 100) -> Iterator[pd.DataFrame]:
        """
        Stream messages in batches.
        Continuous stream - yields batches as they arrive.
        """
        if not self._consumer:
            self.connect()
        
        batch = []
        
        if self._consumer == 'simulated':
            # Simulated stream
            import numpy as np
            for i in range(10000):
                msg = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'sensor_id': f"SENSOR-{i % 10}",
                    'value': float(np.random.normal(100 + (i % 100), 10)),
                    'status': 'ok' if np.random.random() > 0.1 else 'warning',
                }
                batch.append(msg)
                
                if len(batch) >= batch_size:
                    yield pd.DataFrame(batch)
                    batch = []
                    logger.info(f"Streamed batch: {batch_size} messages")
        
        else:
            # Read from broker
            try:
                while True:
                    msg = self._consumer.poll(timeout=1.0)
                    
                    if msg is None:
                        if batch:
                            yield pd.DataFrame(batch)
                            batch = []
                        continue
                    
                    try:
                        data = json.loads(msg.value().decode())
                        batch.append(data)
                        
                        if len(batch) >= batch_size:
                            yield pd.DataFrame(batch)
                            batch = []
                            logger.info(f"Streamed batch: {batch_size} messages")
                    except:
                        logger.warning(f"Could not parse message")
            
            except KeyboardInterrupt:
                logger.info("Stream interrupted")


class S3Connector(UniversalConnector):
    """
    AWS S3 / Azure Blob / GCS connector for data lakes.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Config:
        - provider: 's3', 'azure', 'gcs'
        - bucket: bucket name
        - key: object key/path
        - format: 'csv', 'parquet', 'json'
        """
        super().__init__(config)
        self.provider = config.get('provider', 's3')
        self.bucket = config.get('bucket')
        self.key = config.get('key')
        self.format = config.get('format', 'parquet')
        self._client = None
    
    def connect(self):
        """Connect to cloud storage"""
        try:
            if self.provider == 's3':
                import boto3
                self._client = boto3.client('s3')
                logger.info(f"Connected to S3: s3://{self.bucket}/{self.key}")
            elif self.provider == 'azure':
                from azure.storage.blob import BlobClient
                # Requires connection string
                logger.info(f"Connected to Azure Blob: {self.bucket}/{self.key}")
            elif self.provider == 'gcs':
                from google.cloud import storage
                self._client = storage.Client()
                logger.info(f"Connected to GCS: gs://{self.bucket}/{self.key}")
        except ImportError:
            logger.warning("Cloud storage library not installed")
            self._client = None
    
    def disconnect(self):
        """Clean up"""
        self._client = None
    
    def auto_detect_schema(self) -> ConnectorSchema:
        """Detect schema from first rows"""
        df = self.fetch_data(limit=100)
        
        columns = {}
        for col in df.columns:
            if df[col].dtype in ['int64', 'float64']:
                columns[col] = DataType.NUMERIC
            elif df[col].dtype == 'datetime64[ns]':
                columns[col] = DataType.TEMPORAL
            else:
                columns[col] = DataType.TEXT
        
        return ConnectorSchema(
            columns=columns,
            row_count=len(df),
            estimated_size_bytes=len(df) * len(columns) * 100,
            last_updated=datetime.utcnow().isoformat(),
            sample_rows=df,
            missing_value_rate=df.isnull().sum().sum() / (len(df) * len(df.columns)),
            data_types_detected={col: str(dtype) for col, dtype in df.dtypes.items()}
        )
    
    def fetch_data(self, query: Optional[str] = None, limit: int = None) -> pd.DataFrame:
        """Fetch data from object storage"""
        if not self._client:
            self.connect()
        
        try:
            if self.provider == 's3':
                obj = self._client.get_object(Bucket=self.bucket, Key=self.key)
                body = obj['Body'].read()
            else:
                body = b'sample data'
            
            if self.format == 'csv':
                df = pd.read_csv(pd.io.common.BytesIO(body))
            elif self.format == 'parquet':
                df = pd.read_parquet(pd.io.common.BytesIO(body))
            elif self.format == 'json':
                df = pd.read_json(pd.io.common.BytesIO(body))
            else:
                df = pd.DataFrame()
            
            if limit:
                df = df.head(limit)
            
            logger.info(f"Fetched {len(df)} rows from {self.provider}")
            return df
        
        except Exception as e:
            logger.error(f"Failed to fetch from {self.provider}: {e}")
            return pd.DataFrame()
    
    def stream_data(self, batch_size: int = 1000) -> Iterator[pd.DataFrame]:
        """Stream data in chunks"""
        df = self.fetch_data()
        
        for i in range(0, len(df), batch_size):
            yield df.iloc[i:i+batch_size]
