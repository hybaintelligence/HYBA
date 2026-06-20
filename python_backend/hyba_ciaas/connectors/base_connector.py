"""
Base Universal Connector Interface
All data sources inherit from this
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Iterator, Tuple
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DataType(Enum):
    """Data type classification"""
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    TEMPORAL = "temporal"
    SPATIAL = "spatial"
    TEXT = "text"
    ARRAY = "array"


@dataclass
class ConnectorSchema:
    """Auto-detected schema from data source"""
    columns: Dict[str, DataType]
    row_count: int
    estimated_size_bytes: int
    last_updated: str
    sample_rows: pd.DataFrame
    missing_value_rate: float
    data_types_detected: Dict[str, str]
    
    def summary(self) -> str:
        """Human-readable schema summary"""
        return f"""
Schema Summary:
  Rows: {self.row_count:,}
  Columns: {len(self.columns)}
  Size: {self.estimated_size_bytes / (1024**2):.1f} MB
  Missing rate: {self.missing_value_rate:.1%}
  Last updated: {self.last_updated}
  
Column types:
{chr(10).join(f'  {col}: {dtype.value}' for col, dtype in self.columns.items())}
"""


@dataclass
class NormalizationConfig:
    """Auto-configuration for data normalization"""
    scaling_method: str = "standardize"  # standardize, normalize, robust, log
    missing_value_method: str = "forward_fill"  # forward_fill, interpolate, drop, zero
    categorical_encoding: str = "one_hot"  # one_hot, label, embedding
    temporal_resolution: str = "auto"  # auto, 1s, 1m, 1h, 1d
    feature_engineering: bool = True
    max_features: Optional[int] = None
    min_samples: int = 10


class UniversalConnector(ABC):
    """
    Base connector interface - all data sources implement this.
    
    Provides:
    - Auto schema detection
    - Data normalization
    - PULVINI compression
    - Streaming support
    """
    
    def __init__(self, config: Dict[str, Any], name: str = None, **kwargs):
        self.config = config
        self.name = name or self.__class__.__name__
        self.schema: Optional[ConnectorSchema] = None
        self._connection = None
        self.normalization_config = NormalizationConfig()
        logger.info(f"Initializing connector: {self.name}")
    
    # ===== ABSTRACT METHODS (subclasses must implement) =====
    
    @abstractmethod
    def connect(self):
        """Establish connection to data source"""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Close connection"""
        pass
    
    @abstractmethod
    def auto_detect_schema(self) -> ConnectorSchema:
        """Auto-detect schema from data source"""
        pass
    
    @abstractmethod
    def fetch_data(self, query: Optional[str] = None, limit: int = None) -> pd.DataFrame:
        """Fetch data, return as DataFrame"""
        pass
    
    @abstractmethod
    def stream_data(self, batch_size: int = 1000) -> Iterator[pd.DataFrame]:
        """Stream data in batches"""
        pass
    
    # ===== CONCRETE METHODS (reusable across all connectors) =====
    
    def normalize_data(self, df: pd.DataFrame, config: Optional[NormalizationConfig] = None) -> np.ndarray:
        """
        Normalize data to matrix format for HYBA tensor operations.
        
        Pipeline:
        1. Handle missing values
        2. Encode categorical variables
        3. Scale numerical features
        4. Generate features if enabled
        5. Return as float32 numpy array
        """
        if config is None:
            config = self.normalization_config
        
        df = df.copy()
        
        logger.info(f"Starting normalization: {df.shape}")
        
        # Step 1: Handle missing values
        if config.missing_value_method == "forward_fill":
            df = df.fillna(method='ffill').fillna(method='bfill')
        elif config.missing_value_method == "interpolate":
            df = df.interpolate(method='linear')
        elif config.missing_value_method == "drop":
            df = df.dropna()
        elif config.missing_value_method == "zero":
            df = df.fillna(0)
        
        # Step 2: Encode categoricals
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        if categorical_cols and config.categorical_encoding == "one_hot":
            df = pd.get_dummies(df, columns=categorical_cols, drop_first=False)
        elif categorical_cols and config.categorical_encoding == "label":
            from sklearn.preprocessing import LabelEncoder
            for col in categorical_cols:
                df[col] = LabelEncoder().fit_transform(df[col].astype(str))
        
        # Step 3: Scale numerical features
        numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if numerical_cols:
            if config.scaling_method == "standardize":
                df[numerical_cols] = (df[numerical_cols] - df[numerical_cols].mean()) / (df[numerical_cols].std() + 1e-8)
            elif config.scaling_method == "normalize":
                df[numerical_cols] = (df[numerical_cols] - df[numerical_cols].min()) / (df[numerical_cols].max() - df[numerical_cols].min() + 1e-8)
            elif config.scaling_method == "robust":
                from sklearn.preprocessing import RobustScaler
                df[numerical_cols] = RobustScaler().fit_transform(df[numerical_cols])
        
        # Step 4: Generate features
        if config.feature_engineering and len(numerical_cols) >= 2:
            # Auto-generate ratios
            for i in range(min(len(numerical_cols) - 1, 5)):  # Limit to first 5 to avoid explosion
                for j in range(i + 1, min(i + 3, len(numerical_cols))):  # Limit pairwise combos
                    col1, col2 = numerical_cols[i], numerical_cols[j]
                    ratio_col = f"{col1}_over_{col2}"
                    df[ratio_col] = df[col1] / (df[col2] + 1e-8)
        
        # Step 5: Limit features if specified
        if config.max_features:
            df = df.iloc[:, :config.max_features]
        
        # Step 6: Convert to numpy
        result = df.values.astype(np.float32)
        logger.info(f"Normalization complete: {result.shape}")
        
        return result
    
    def ingest_and_normalize(self, query: str = None, compression: bool = True) -> Dict[str, Any]:
        """
        End-to-end ingestion pipeline.
        
        Returns:
        {
            'data': normalized numpy array,
            'schema': ConnectorSchema,
            'shape': (n_samples, n_features),
            'compression': {'ratio': 2.3, 'fold_depth': 5}
        }
        """
        logger.info(f"Starting ingestion pipeline for {self.name}")
        
        # 1. Connect
        self.connect()
        
        # 2. Auto-detect schema
        self.schema = self.auto_detect_schema()
        logger.info(f"Schema detected:\n{self.schema.summary()}")
        
        # 3. Fetch data
        df = self.fetch_data(query=query)
        logger.info(f"Fetched {len(df)} rows, {len(df.columns)} columns")
        
        # 4. Normalize
        normalized = self.normalize_data(df)
        logger.info(f"Normalized to shape {normalized.shape}")
        
        # 5. Compress (optional)
        compression_info = None
        if compression:
            try:
                from pythia_mining.pulvini import PHIFoldingCompressor
                compressor = PHIFoldingCompressor(compression_target=0.5)
                compressed = compressor.compress(normalized)
                compression_info = {
                    'ratio': compressor.compression_ratio,
                    'fold_depth': compressor.fold_depth,
                    'error_bound': compressor.error_bound
                }
                logger.info(f"PULVINI compression: {compression_info['ratio']:.2f}x")
            except ImportError:
                logger.warning("PULVINI compressor not available, skipping compression")
        
        self.disconnect()
        
        return {
            'data': normalized,
            'schema': self.schema,
            'shape': normalized.shape,
            'compression': compression_info,
            'source': self.name,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def stream_and_normalize(self, batch_size: int = 1000) -> Iterator[Dict[str, Any]]:
        """
        Stream data in batches with normalization.
        Yields normalized numpy arrays.
        """
        self.connect()
        self.schema = self.auto_detect_schema()
        
        try:
            for batch_df in self.stream_data(batch_size=batch_size):
                normalized = self.normalize_data(batch_df)
                yield {
                    'data': normalized,
                    'shape': normalized.shape,
                    'timestamp': datetime.utcnow().isoformat()
                }
        finally:
            self.disconnect()
