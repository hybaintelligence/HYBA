"""
Universal SQL Connector
Supports: PostgreSQL, MySQL, Snowflake, BigQuery, Oracle, SQL Server
"""

from typing import Dict, List, Any, Optional, Iterator
import pandas as pd
import sqlalchemy
from sqlalchemy import inspect, text
import logging

from .base_connector import UniversalConnector, ConnectorSchema, DataType

logger = logging.getLogger(__name__)


class SQLConnector(UniversalConnector):
    """
    Universal SQL database connector.
    Auto-detects and handles multiple database types.
    """
    
    DRIVER_MAP = {
        'postgresql': 'postgresql+psycopg2',
        'mysql': 'mysql+pymysql',
        'oracle': 'oracle+cx_oracle',
        'snowflake': 'snowflake',
        'bigquery': 'bigquery',
        'sqlserver': 'mssql+pyodbc',
    }
    
    def __init__(self, config: Dict[str, Any]):
        """
        Config must contain:
        - db_type: 'postgresql', 'mysql', 'snowflake', etc.
        - host/server, database, user, password
        - Optional: port, query (default table query)
        """
        super().__init__(config)
        self.db_type = config.get('db_type', 'postgresql').lower()
        self.host = config.get('host') or config.get('server')
        self.database = config.get('database')
        self.user = config.get('user')
        self.password = config.get('password')
        self.port = config.get('port', self._default_port())
        self.query = config.get('query', f"SELECT * FROM {config.get('table', 'data')}")
        self.engine = None
    
    def _default_port(self) -> int:
        """Get default port for database type"""
        ports = {
            'postgresql': 5432,
            'mysql': 3306,
            'oracle': 1521,
            'sqlserver': 1433,
        }
        return ports.get(self.db_type, 5432)
    
    def _build_url(self) -> str:
        """Build SQLAlchemy connection URL"""
        driver = self.DRIVER_MAP.get(self.db_type, 'postgresql+psycopg2')
        
        if self.db_type == 'snowflake':
            # Snowflake format
            return f"{driver}://{self.user}:{self.password}@{self.host}/{self.database}"
        elif self.db_type == 'bigquery':
            # BigQuery format (project-id)
            return f"{driver}://{self.database}"
        else:
            # Standard format
            return f"{driver}://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    def connect(self):
        """Establish database connection"""
        try:
            url = self._build_url()
            self.engine = sqlalchemy.create_engine(url)
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info(f"Connected to {self.db_type} database: {self.database}")
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise
    
    def disconnect(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
            logger.info("Disconnected from database")
    
    def auto_detect_schema(self) -> ConnectorSchema:
        """
        Auto-detect schema from database.
        Inspects table structure and infers data types.
        """
        if not self.engine:
            self.connect()
        
        # Extract table name from query (basic parsing)
        table_name = self._extract_table_name()
        
        inspector = inspect(self.engine)
        columns_info = inspector.get_columns(table_name)
        
        # Sample data
        df_sample = pd.read_sql(f"SELECT * FROM {table_name} LIMIT 100", self.engine)
        row_count = pd.read_sql(f"SELECT COUNT(*) as cnt FROM {table_name}", self.engine).iloc[0, 0]
        
        # Infer data types
        columns_dict = {}
        for col in columns_info:
            col_type = str(col['type']).lower()
            if 'int' in col_type or 'numeric' in col_type or 'float' in col_type or 'decimal' in col_type:
                columns_dict[col['name']] = DataType.NUMERIC
            elif 'date' in col_type or 'time' in col_type:
                columns_dict[col['name']] = DataType.TEMPORAL
            elif 'char' in col_type or 'text' in col_type:
                columns_dict[col['name']] = DataType.TEXT
            else:
                columns_dict[col['name']] = DataType.CATEGORICAL
        
        # Calculate missing rate
        missing_rate = df_sample.isnull().sum().sum() / (len(df_sample) * len(df_sample.columns))
        
        # Estimate size (rough)
        estimated_size = row_count * len(columns_dict) * 100  # ~100 bytes per field
        
        return ConnectorSchema(
            columns=columns_dict,
            row_count=row_count,
            estimated_size_bytes=estimated_size,
            last_updated=pd.Timestamp.now().isoformat(),
            sample_rows=df_sample,
            missing_value_rate=missing_rate,
            data_types_detected={col['name']: str(col['type']) for col in columns_info}
        )
    
    def _extract_table_name(self) -> str:
        """Extract table name from query (basic)"""
        query_upper = self.query.upper()
        if 'FROM' in query_upper:
            parts = query_upper.split('FROM')
            table_part = parts[1].strip().split()[0]
            return table_part.strip('`"[]')
        return 'data'
    
    def fetch_data(self, query: Optional[str] = None, limit: int = None) -> pd.DataFrame:
        """Fetch data from database"""
        if not self.engine:
            self.connect()
        
        sql = query or self.query
        if limit:
            sql += f" LIMIT {limit}"
        
        logger.info(f"Executing query: {sql[:100]}...")
        df = pd.read_sql(sql, self.engine)
        logger.info(f"Fetched {len(df)} rows")
        
        return df
    
    def stream_data(self, batch_size: int = 1000) -> Iterator[pd.DataFrame]:
        """Stream data in batches"""
        if not self.engine:
            self.connect()
        
        total_rows = 0
        offset = 0
        
        while True:
            sql = f"{self.query} LIMIT {batch_size} OFFSET {offset}"
            df_batch = pd.read_sql(sql, self.engine)
            
            if df_batch.empty:
                break
            
            logger.info(f"Streamed batch: rows {offset}-{offset + len(df_batch)}")
            yield df_batch
            
            total_rows += len(df_batch)
            offset += batch_size
        
        logger.info(f"Stream complete: {total_rows} total rows")
