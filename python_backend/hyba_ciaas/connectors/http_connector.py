"""
Generic HTTP/REST API Connector
For government APIs, data.gov, APIs.gov, and any REST endpoint
"""

from typing import Dict, List, Any, Optional, Iterator
import pandas as pd
import numpy as np
import logging
import requests
import json
from urllib.parse import urljoin
from datetime import datetime

from .base_connector import UniversalConnector, ConnectorSchema, DataType

logger = logging.getLogger(__name__)


class HTTPConnector(UniversalConnector):
    """
    Generic HTTP/REST API connector.
    
    Supports:
    - Government APIs (NOAA, USGS, etc.)
    - data.gov, APIs.gov
    - Authentication (API key, OAuth, Basic)
    - Pagination
    - Rate limiting
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Config:
        - endpoint: base URL
        - method: GET, POST, etc.
        - headers: custom headers (User-Agent, etc.)
        - auth: {'type': 'api_key', 'key': 'xxx'} or {'type': 'basic', 'user': 'xxx', 'pass': 'xxx'}
        - params: query parameters
        - pagination: {'page_param': 'page', 'size_param': 'limit'}
        """
        super().__init__(config)
        self.endpoint = config.get('endpoint')
        self.method = config.get('method', 'GET').upper()
        self.headers = config.get('headers', {'User-Agent': 'HYBA-CIaaS/1.0'})
        self.auth = config.get('auth')
        self.params = config.get('params', {})
        self.pagination = config.get('pagination', {'page_param': 'page', 'size_param': 'limit'})
        self.rate_limit = config.get('rate_limit', 10)  # requests per second
        self._session = None
    
    def connect(self):
        """Create HTTP session with authentication"""
        self._session = requests.Session()
        
        # Add authentication if specified
        if self.auth:
            if self.auth.get('type') == 'api_key':
                self.headers['Authorization'] = f"Bearer {self.auth.get('key')}"
            elif self.auth.get('type') == 'basic':
                from requests.auth import HTTPBasicAuth
                self._session.auth = HTTPBasicAuth(self.auth.get('user'), self.auth.get('pass'))
        
        self._session.headers.update(self.headers)
        logger.info(f"HTTP session initialized for {self.endpoint}")
    
    def disconnect(self):
        """Close HTTP session"""
        if self._session:
            self._session.close()
    
    def auto_detect_schema(self) -> ConnectorSchema:
        """Auto-detect schema from first API response"""
        try:
            response = self._session.get(self.endpoint, params={**self.params, 'limit': 10})
            response.raise_for_status()
            
            data = response.json()
            
            # Handle different response formats
            if isinstance(data, dict):
                if 'data' in data:
                    data = data['data']
                elif 'results' in data:
                    data = data['results']
            
            if isinstance(data, list) and len(data) > 0:
                df_sample = pd.DataFrame(data[:10])
            elif isinstance(data, dict):
                df_sample = pd.DataFrame([data])
            else:
                df_sample = pd.DataFrame()
            
            # Infer columns
            columns = {}
            for col in df_sample.columns:
                if df_sample[col].dtype in [np.int64, np.float64]:
                    columns[col] = DataType.NUMERIC
                elif df_sample[col].dtype == 'datetime64[ns]':
                    columns[col] = DataType.TEMPORAL
                else:
                    columns[col] = DataType.TEXT
            
            return ConnectorSchema(
                columns=columns,
                row_count=100000,  # Estimate
                estimated_size_bytes=100000 * len(columns) * 100,
                last_updated=datetime.utcnow().isoformat(),
                sample_rows=df_sample,
                missing_value_rate=0.05,
                data_types_detected={col: str(dtype) for col, dtype in df_sample.dtypes.items()}
            )
        
        except Exception as e:
            logger.error(f"Schema detection failed: {e}")
            return ConnectorSchema(
                columns={'data': DataType.TEXT},
                row_count=0,
                estimated_size_bytes=0,
                last_updated=datetime.utcnow().isoformat(),
                sample_rows=pd.DataFrame(),
                missing_value_rate=0,
                data_types_detected={}
            )
    
    def fetch_data(self, query: Optional[str] = None, limit: int = None) -> pd.DataFrame:
        """Fetch data from API"""
        if not self._session:
            self.connect()
        
        # Build request parameters
        params = {**self.params}
        if query:
            params.update(json.loads(query) if query.startswith('{') else {'q': query})
        if limit:
            params[self.pagination['size_param']] = limit
        
        try:
            logger.info(f"GET {self.endpoint} with params: {params}")
            response = self._session.request(self.method, self.endpoint, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Handle nested responses
            if isinstance(data, dict):
                if 'data' in data:
                    data = data['data']
                elif 'results' in data:
                    data = data['results']
                elif 'items' in data:
                    data = data['items']
            
            if isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                df = pd.DataFrame([data])
            
            logger.info(f"Fetched {len(df)} records from API")
            return df
        
        except Exception as e:
            logger.error(f"API request failed: {e}")
            return pd.DataFrame()
    
    def stream_data(self, batch_size: int = 1000) -> Iterator[pd.DataFrame]:
        """Stream data in batches with pagination"""
        if not self._session:
            self.connect()
        
        page = 1
        total_fetched = 0
        
        while True:
            params = {
                **self.params,
                self.pagination['page_param']: page,
                self.pagination['size_param']: batch_size
            }
            
            try:
                response = self._session.request(self.method, self.endpoint, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                # Extract data from nested structures
                if isinstance(data, dict):
                    if 'data' in data:
                        data = data['data']
                    elif 'results' in data:
                        data = data['results']
                
                if not data:
                    break
                
                df = pd.DataFrame(data)
                total_fetched += len(df)
                
                logger.info(f"Streamed page {page}: {len(df)} records (total: {total_fetched})")
                yield df
                
                page += 1
            
            except Exception as e:
                logger.error(f"Stream error: {e}")
                break


class GovernmentAPIConnector(HTTPConnector):
    """
    Pre-configured government API connectors.
    NOAA, USGS, Census, etc.
    """
    
    # Pre-built government API endpoints
    APIS = {
        'noaa_weather': {
            'endpoint': 'https://api.weather.gov/points/{lat},{lon}',
            'params': {},
            'headers': {'User-Agent': '(HYBA-CIaaS, contact@hyba.ai)'},
        },
        'usgs_earthquakes': {
            'endpoint': 'https://earthquake.usgs.gov/fdsnws/event/1/query',
            'params': {'format': 'geojson'},
            'pagination': {'page_param': 'offset', 'size_param': 'limit'},
        },
        'census_acs': {
            'endpoint': 'https://api.census.gov/data/2021/acs/acs5',
            'auth': {'type': 'api_key'},  # Requires user to provide key
        },
        'energy_eia': {
            'endpoint': 'https://api.eia.gov/v1',
            'auth': {'type': 'api_key'},
        },
    }
    
    @classmethod
    def create_government_connector(cls, api_name: str, **kwargs) -> 'GovernmentAPIConnector':
        """Factory for government API connectors"""
        if api_name not in cls.APIS:
            raise ValueError(f"Unknown government API: {api_name}")
        
        config = {**cls.APIS[api_name], **kwargs}
        return cls(config)
