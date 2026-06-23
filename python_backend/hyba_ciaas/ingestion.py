"""Central, sector-agnostic data ingestion for HYBA CIaaS."""

from __future__ import annotations

import hashlib
import importlib
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Mapping,
    Optional,
    Tuple,
    Union,
)

import numpy as np
import pandas as pd

from .connectors.base_connector import (
    ConnectorSchema,
    DataType,
    NormalizationConfig,
    UniversalConnector,
)

logger = logging.getLogger(__name__)
ConnectorFactory = Union[type, Callable[[Dict[str, Any]], UniversalConnector], str]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_json(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(k): _safe_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_safe_json(v) for v in value]
    return value


def _json_string(value: Any) -> str:
    return json.dumps(_safe_json(value), sort_keys=True, default=str)


@dataclass(frozen=True)
class DataSourceSpec:
    """Source contract accepted by the central ingestion service."""

    source_type: str
    config: Dict[str, Any] = field(default_factory=dict)
    sector: str = "sector_agnostic"
    source_id: Optional[str] = None
    data_format: Optional[str] = None
    tenant_id: Optional[str] = None
    purpose: Optional[str] = None
    privacy_classification: str = "unclassified"
    tags: Tuple[str, ...] = field(default_factory=tuple)
    query: Optional[str] = None
    limit: Optional[int] = None
    batch_size: int = 1000
    normalize: bool = True
    compression: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "DataSourceSpec":
        known = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        payload_dict = dict(payload)
        config = dict(payload_dict.get("config") or {})
        for key, value in payload_dict.items():
            if key not in known:
                config.setdefault(key, value)

        tags = payload_dict.get("tags", ())
        tags = (tags,) if isinstance(tags, str) else tuple(tags or ())

        return cls(
            source_type=str(payload_dict["source_type"]),
            config=config,
            sector=str(payload_dict.get("sector", "sector_agnostic")),
            source_id=payload_dict.get("source_id"),
            data_format=payload_dict.get("data_format"),
            tenant_id=payload_dict.get("tenant_id"),
            purpose=payload_dict.get("purpose"),
            privacy_classification=str(
                payload_dict.get("privacy_classification", "unclassified")
            ),
            tags=tags,
            query=payload_dict.get("query"),
            limit=payload_dict.get("limit"),
            batch_size=int(payload_dict.get("batch_size", 1000)),
            normalize=bool(payload_dict.get("normalize", True)),
            compression=bool(payload_dict.get("compression", False)),
            metadata=dict(payload_dict.get("metadata") or {}),
        )

    @property
    def canonical_source_id(self) -> str:
        if self.source_id:
            return self.source_id
        if self.tenant_id:
            return f"{self.tenant_id}:{self.source_type}"
        return self.source_type


@dataclass
class DataQualityReport:
    row_count: int
    column_count: int
    missing_value_rate: float
    duplicate_row_rate: float
    empty_column_count: int
    high_cardinality_columns: List[str]
    score: float
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "row_count": self.row_count,
            "column_count": self.column_count,
            "missing_value_rate": self.missing_value_rate,
            "duplicate_row_rate": self.duplicate_row_rate,
            "empty_column_count": self.empty_column_count,
            "high_cardinality_columns": list(self.high_cardinality_columns),
            "score": self.score,
            "warnings": list(self.warnings),
        }


@dataclass
class LineageEvent:
    step: str
    status: str = "ok"
    timestamp: str = field(default_factory=_utc_now)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "status": self.status,
            "timestamp": self.timestamp,
            "details": _safe_json(self.details),
        }


@dataclass
class IngestionEnvelope:
    """Canonical output emitted by HYBA central ingestion."""

    run_id: str
    source_id: str
    source_type: str
    sector: str
    connector_name: str
    schema: ConnectorSchema
    quality: DataQualityReport
    data: pd.DataFrame
    normalized_data: Optional[np.ndarray]
    raw_shape: Tuple[int, int]
    normalized_shape: Optional[Tuple[int, int]]
    started_at: str
    completed_at: str
    lineage: List[LineageEvent]
    compression: Optional[Dict[str, Any]] = None
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def schema_as_dict(self) -> Dict[str, Any]:
        sample = self.schema.sample_rows
        return {
            "columns": {
                name: dtype.value for name, dtype in self.schema.columns.items()
            },
            "row_count": self.schema.row_count,
            "estimated_size_bytes": self.schema.estimated_size_bytes,
            "last_updated": self.schema.last_updated,
            "missing_value_rate": self.schema.missing_value_rate,
            "data_types_detected": dict(self.schema.data_types_detected),
            "sample_rows": (
                sample.head(5).to_dict(orient="records")
                if isinstance(sample, pd.DataFrame)
                else []
            ),
        }

    def to_service_payload(self, include_data: bool = False) -> Dict[str, Any]:
        payload = {
            "run_id": self.run_id,
            "source_id": self.source_id,
            "source_type": self.source_type,
            "sector": self.sector,
            "connector_name": self.connector_name,
            "raw_shape": self.raw_shape,
            "normalized_shape": self.normalized_shape,
            "schema": self.schema_as_dict(),
            "quality": self.quality.to_dict(),
            "compression": _safe_json(self.compression),
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "lineage": [event.to_dict() for event in self.lineage],
            "warnings": list(self.warnings),
            "metadata": _safe_json(self.metadata),
        }
        if include_data:
            payload["records"] = self.data.to_dict(orient="records")
            payload["normalized_data"] = (
                self.normalized_data.tolist()
                if self.normalized_data is not None
                else None
            )
        return payload


class DataFrameConnector(UniversalConnector):
    """Universal fallback for inline records, arrays, text, JSON, CSV, and local files."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, name=config.get("name", "DataFrameConnector"))
        self._df: Optional[pd.DataFrame] = None

    def connect(self):
        self._df = self._load_dataframe()

    def disconnect(self):
        self._df = None

    def auto_detect_schema(self) -> ConnectorSchema:
        df = self._ensure_dataframe()
        cells = len(df) * len(df.columns)
        columns = {column: self._infer_type(df[column]) for column in df.columns}
        return ConnectorSchema(
            columns=columns,
            row_count=len(df),
            estimated_size_bytes=int(df.memory_usage(index=True, deep=True).sum()),
            last_updated=_utc_now(),
            sample_rows=df.head(100),
            missing_value_rate=float(df.isna().sum().sum() / cells) if cells else 0.0,
            data_types_detected={
                column: str(dtype) for column, dtype in df.dtypes.items()
            },
        )

    def fetch_data(
        self, query: Optional[str] = None, limit: int = None
    ) -> pd.DataFrame:
        df = self._ensure_dataframe()
        if query:
            df = df.query(query)
        return df.head(limit).copy() if limit else df.copy()

    def stream_data(self, batch_size: int = 1000) -> Iterator[pd.DataFrame]:
        df = self._ensure_dataframe()
        for start in range(0, len(df), batch_size):
            yield df.iloc[start : start + batch_size].copy()

    def _ensure_dataframe(self) -> pd.DataFrame:
        if self._df is None:
            self.connect()
        assert self._df is not None
        return self._df

    def _load_dataframe(self) -> pd.DataFrame:
        config = self.config
        data = config.get(
            "data", config.get("records", config.get("rows", config.get("array")))
        )
        fmt = str(config.get("format") or config.get("data_format") or "").lower()

        if isinstance(data, pd.DataFrame):
            return data.copy()
        if isinstance(data, np.ndarray):
            return self._from_array(data)
        if isinstance(data, (list, tuple)):
            if not data:
                return pd.DataFrame()
            if all(isinstance(item, Mapping) for item in data):
                return pd.json_normalize(list(data))
            return pd.DataFrame(data)
        if isinstance(data, Mapping):
            return (
                pd.json_normalize(data)
                if any(isinstance(v, (list, tuple, dict)) for v in data.values())
                else pd.DataFrame([dict(data)])
            )
        if isinstance(data, str):
            text = data.strip()
            if fmt == "csv" or ("\n" in text and "," in text.splitlines()[0]):
                from io import StringIO

                return pd.read_csv(StringIO(data))
            if fmt == "json" or text.startswith("{") or text.startswith("["):
                return self._load_dataframe_from_value(json.loads(data))
            return pd.DataFrame({"text": [data]})

        path_value = config.get("path") or config.get("file_path")
        return self._load_file(Path(path_value), fmt) if path_value else pd.DataFrame()

    def _load_dataframe_from_value(self, value: Any) -> pd.DataFrame:
        if isinstance(value, Mapping):
            return pd.json_normalize(value)
        if isinstance(value, list):
            return (
                pd.json_normalize(value)
                if all(isinstance(item, Mapping) for item in value)
                else pd.DataFrame(value)
            )
        if isinstance(value, np.ndarray):
            return self._from_array(value)
        return pd.DataFrame({"value": [value]})

    def _load_file(self, path: Path, fmt: str) -> pd.DataFrame:
        fmt = fmt or path.suffix.lower().lstrip(".")
        if fmt == "csv":
            return pd.read_csv(path)
        if fmt in {"json", "jsonl", "ndjson"}:
            return pd.read_json(path, lines=fmt in {"jsonl", "ndjson"})
        if fmt == "parquet":
            return pd.read_parquet(path)
        if fmt in {"xlsx", "xls", "excel"}:
            return pd.read_excel(path)
        if fmt in {"txt", "text"}:
            return pd.DataFrame({"text": path.read_text(encoding="utf-8").splitlines()})
        raise ValueError(f"Unsupported local data format: {fmt or path.suffix}")

    @staticmethod
    def _from_array(data: np.ndarray) -> pd.DataFrame:
        array = np.asarray(data)
        if array.ndim == 0:
            return pd.DataFrame({"value": [array.item()]})
        if array.ndim == 1:
            return pd.DataFrame({"value": array})
        if array.ndim == 2:
            return pd.DataFrame(
                array, columns=[f"feature_{i}" for i in range(array.shape[1])]
            )
        flat = array.reshape(array.shape[0], -1)
        return pd.DataFrame(
            flat, columns=[f"feature_{i}" for i in range(flat.shape[1])]
        )

    @staticmethod
    def _infer_type(series: pd.Series) -> DataType:
        if pd.api.types.is_numeric_dtype(series):
            return DataType.NUMERIC
        if pd.api.types.is_datetime64_any_dtype(series):
            return DataType.TEMPORAL
        non_null = series.dropna()
        if non_null.empty:
            return DataType.TEXT
        sample = non_null.iloc[0]
        if isinstance(sample, (list, tuple, np.ndarray, dict)):
            return DataType.ARRAY
        text = non_null.astype(str)
        if text.str.match(r"^-?\d+(\.\d+)?$").mean() > 0.9:
            return DataType.NUMERIC
        if text.str.match(r"^\d{4}-\d{2}-\d{2}").mean() > 0.5:
            return DataType.TEMPORAL
        if text.nunique(dropna=True) <= max(20, int(len(text) * 0.2)):
            return DataType.CATEGORICAL
        return DataType.TEXT


class ConnectorRegistry:
    """Central source-type registry for all HYBA ingestion connectors."""

    def __init__(self):
        self._factories: Dict[str, ConnectorFactory] = {}
        self._aliases: Dict[str, str] = {}

    @classmethod
    def with_defaults(cls) -> "ConnectorRegistry":
        registry = cls()
        registry.register(
            "inline", DataFrameConnector, ("records", "rows", "dataframe", "array")
        )
        registry.register(
            "file",
            DataFrameConnector,
            ("csv", "json", "jsonl", "parquet", "excel", "text"),
        )
        registry.register(
            "sql",
            "hyba_ciaas.connectors.sql_connector.SQLConnector",
            (
                "database",
                "postgres",
                "postgresql",
                "mysql",
                "oracle",
                "snowflake",
                "bigquery",
                "sqlserver",
            ),
        )
        registry.register(
            "stream",
            "hyba_ciaas.connectors.kafka_connector.KafkaConnector",
            ("kafka", "kinesis", "eventhub", "event_stream", "events"),
        )
        registry.register(
            "object_store",
            "hyba_ciaas.connectors.kafka_connector.S3Connector",
            ("s3", "adls", "gcs", "data_lake", "blob"),
        )
        registry.register(
            "http",
            "hyba_ciaas.connectors.http_connector.HTTPConnector",
            ("api", "rest", "graphql", "webhook"),
        )
        registry.register(
            "scada",
            "hyba_ciaas.connectors.scada_connector.SCADAConnector",
            ("industrial_iot", "iot", "opcua", "modbus", "energy"),
        )
        registry.register(
            "pubchem",
            "hyba_ciaas.connectors.pubchem_connector.PubChemConnector",
            ("chemistry", "molecule", "compound", "drug_discovery"),
        )
        registry.register(
            "protein",
            "hyba_ciaas.connectors.protein_connector.ProteinConnector",
            ("fasta", "pdb", "uniprot", "bioinformatics"),
        )
        return registry

    def register(
        self, source_type: str, factory: ConnectorFactory, aliases: Iterable[str] = ()
    ) -> None:
        canonical = self._normalise(source_type)
        self._factories[canonical] = factory
        self._aliases[canonical] = canonical
        for alias in aliases:
            self._aliases[self._normalise(alias)] = canonical

    def resolve(self, source_type: str) -> str:
        key = self._normalise(source_type)
        if key in self._aliases:
            return self._aliases[key]
        if key in self._factories:
            return key
        raise KeyError(
            f"Unknown ingestion source_type={source_type!r}; registered={sorted(self._factories)}"
        )

    def create_connector(self, spec: DataSourceSpec) -> UniversalConnector:
        canonical = self.resolve(spec.source_type)
        factory = self._factories[canonical]
        if isinstance(factory, str):
            module_path, class_name = factory.rsplit(".", 1)
            factory = getattr(importlib.import_module(module_path), class_name)
        config = dict(spec.config)
        config.setdefault("source_id", spec.canonical_source_id)
        config.setdefault("sector", spec.sector)
        config.setdefault("data_format", spec.data_format)
        connector = factory(config)  # type: ignore[misc]
        if not isinstance(connector, UniversalConnector):
            raise TypeError(
                f"Factory for {canonical!r} did not return UniversalConnector"
            )
        return connector

    def list_source_types(self) -> Dict[str, List[str]]:
        aliases: Dict[str, List[str]] = {
            source_type: [] for source_type in self._factories
        }
        for alias, canonical in self._aliases.items():
            if alias != canonical:
                aliases.setdefault(canonical, []).append(alias)
        return {key: sorted(value) for key, value in sorted(aliases.items())}

    @staticmethod
    def _normalise(value: str) -> str:
        return value.strip().lower().replace("-", "_").replace(" ", "_")


class DataIngestionService:
    """Single HYBA entry point for batch and streaming ingestion."""

    def __init__(
        self,
        registry: Optional[ConnectorRegistry] = None,
        normalization_config: Optional[NormalizationConfig] = None,
        max_text_categories: int = 64,
    ):
        self.registry = registry or ConnectorRegistry.with_defaults()
        self.normalization_config = normalization_config or NormalizationConfig()
        self.max_text_categories = max_text_categories

    def ingest(
        self,
        source: Union[DataSourceSpec, Mapping[str, Any]],
        query: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> IngestionEnvelope:
        spec = (
            source
            if isinstance(source, DataSourceSpec)
            else DataSourceSpec.from_mapping(source)
        )
        run_id = str(uuid.uuid4())
        started_at = _utc_now()
        lineage = [
            LineageEvent(
                "ingestion_requested",
                details={
                    "source_id": spec.canonical_source_id,
                    "source_type": spec.source_type,
                    "sector": spec.sector,
                },
            )
        ]
        warnings: List[str] = []
        connector = self.registry.create_connector(spec)

        try:
            connector.connect()
            lineage.append(
                LineageEvent(
                    "connector_connected",
                    details={"connector": connector.__class__.__name__},
                )
            )
            schema = connector.auto_detect_schema()
            lineage.append(
                LineageEvent(
                    "schema_detected",
                    details={"rows": schema.row_count, "columns": len(schema.columns)},
                )
            )
            raw_df = connector.fetch_data(
                query=query or spec.query, limit=limit or spec.limit
            )
            raw_df = (
                raw_df if isinstance(raw_df, pd.DataFrame) else pd.DataFrame(raw_df)
            )
            lineage.append(
                LineageEvent("data_fetched", details={"shape": tuple(raw_df.shape)})
            )

            quality = self.assess_quality(raw_df)
            warnings.extend(quality.warnings)
            prepared_df, prep_warnings = self.prepare_for_normalization(raw_df)
            warnings.extend(prep_warnings)
            lineage.append(
                LineageEvent(
                    "data_prepared",
                    details={"prepared_shape": tuple(prepared_df.shape)},
                )
            )

            normalized: Optional[np.ndarray]
            normalized_shape: Optional[Tuple[int, int]]
            if spec.normalize:
                normalized = (
                    np.empty((0, 0), dtype=np.float32)
                    if prepared_df.empty
                    else connector.normalize_data(
                        prepared_df, self.normalization_config
                    )
                )
                normalized_shape = tuple(normalized.shape)
                lineage.append(
                    LineageEvent("data_normalized", details={"shape": normalized_shape})
                )
            else:
                normalized = None
                normalized_shape = None
                lineage.append(LineageEvent("normalization_skipped"))

            compression_info = (
                self._try_compress(normalized, warnings)
                if spec.compression and normalized is not None and normalized.size
                else None
            )
            if spec.compression:
                lineage.append(
                    LineageEvent(
                        "compression_attempted", details=compression_info or {}
                    )
                )

            return IngestionEnvelope(
                run_id=run_id,
                source_id=spec.canonical_source_id,
                source_type=self.registry.resolve(spec.source_type),
                sector=spec.sector,
                connector_name=connector.__class__.__name__,
                schema=schema,
                quality=quality,
                data=prepared_df,
                normalized_data=normalized,
                raw_shape=tuple(raw_df.shape),
                normalized_shape=normalized_shape,
                started_at=started_at,
                completed_at=_utc_now(),
                lineage=lineage,
                compression=compression_info,
                warnings=warnings,
                metadata={
                    "tenant_id": spec.tenant_id,
                    "purpose": spec.purpose,
                    "privacy_classification": spec.privacy_classification,
                    "tags": list(spec.tags),
                    **spec.metadata,
                },
            )
        except Exception as exc:
            lineage.append(
                LineageEvent("ingestion_failed", "error", details={"error": str(exc)})
            )
            logger.exception(
                "HYBA central ingestion failed for %s", spec.canonical_source_id
            )
            raise
        finally:
            connector.disconnect()

    def ingest_many(
        self, sources: Iterable[Union[DataSourceSpec, Mapping[str, Any]]]
    ) -> List[IngestionEnvelope]:
        return [self.ingest(source) for source in sources]

    def stream(
        self,
        source: Union[DataSourceSpec, Mapping[str, Any]],
        batch_size: Optional[int] = None,
        max_batches: Optional[int] = None,
    ) -> Iterator[IngestionEnvelope]:
        spec = (
            source
            if isinstance(source, DataSourceSpec)
            else DataSourceSpec.from_mapping(source)
        )
        connector = self.registry.create_connector(spec)
        started_at = _utc_now()
        try:
            connector.connect()
            schema = connector.auto_detect_schema()
            for batch_index, raw_df in enumerate(
                connector.stream_data(batch_size=batch_size or spec.batch_size)
            ):
                if max_batches is not None and batch_index >= max_batches:
                    break
                raw_df = (
                    raw_df if isinstance(raw_df, pd.DataFrame) else pd.DataFrame(raw_df)
                )
                quality = self.assess_quality(raw_df)
                prepared_df, warnings = self.prepare_for_normalization(raw_df)
                if spec.normalize:
                    normalized = (
                        np.empty((0, 0), dtype=np.float32)
                        if prepared_df.empty
                        else connector.normalize_data(
                            prepared_df, self.normalization_config
                        )
                    )
                    normalized_shape = tuple(normalized.shape)
                else:
                    normalized = None
                    normalized_shape = None
                yield IngestionEnvelope(
                    run_id=str(uuid.uuid4()),
                    source_id=spec.canonical_source_id,
                    source_type=self.registry.resolve(spec.source_type),
                    sector=spec.sector,
                    connector_name=connector.__class__.__name__,
                    schema=schema,
                    quality=quality,
                    data=prepared_df,
                    normalized_data=normalized,
                    raw_shape=tuple(raw_df.shape),
                    normalized_shape=normalized_shape,
                    started_at=started_at,
                    completed_at=_utc_now(),
                    lineage=[
                        LineageEvent(
                            "stream_batch_ingested",
                            details={"batch_index": batch_index},
                        )
                    ],
                    warnings=warnings + quality.warnings,
                    metadata={
                        "batch_index": batch_index,
                        "tenant_id": spec.tenant_id,
                        "purpose": spec.purpose,
                        "privacy_classification": spec.privacy_classification,
                        "tags": list(spec.tags),
                        **spec.metadata,
                    },
                )
        finally:
            connector.disconnect()

    def prepare_for_normalization(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, List[str]]:
        warnings: List[str] = []
        if df is None or df.empty:
            return pd.DataFrame(), warnings

        prepared = pd.json_normalize(df.to_dict(orient="records"))
        prepared.columns = [str(column) for column in prepared.columns]

        for column in list(prepared.columns):
            series = prepared[column]
            if pd.api.types.is_bool_dtype(series):
                prepared[column] = series.astype("Int64")
                continue
            if pd.api.types.is_datetime64_any_dtype(series):
                prepared[column] = (
                    pd.to_datetime(series, errors="coerce").astype("int64")
                    / 1_000_000_000
                )
                continue
            if series.dtype != object:
                continue

            non_null = series.dropna()
            if non_null.empty:
                continue
            if non_null.map(
                lambda value: isinstance(value, (Mapping, list, tuple, np.ndarray))
            ).any():
                prepared[column] = series.map(
                    lambda value: (
                        _json_string(value)
                        if isinstance(value, (Mapping, list, tuple, np.ndarray))
                        else value
                    )
                )

            parsed_datetime = pd.to_datetime(
                prepared[column], errors="coerce", utc=True
            )
            if parsed_datetime.notna().mean() >= 0.85:
                prepared[column] = parsed_datetime.astype("int64") / 1_000_000_000
                continue

            text_values = prepared[column].dropna().astype(str)
            unique_count = text_values.nunique(dropna=True)
            mean_length = (
                float(text_values.str.len().mean()) if len(text_values) else 0.0
            )
            if unique_count > self.max_text_categories or mean_length > 80:
                prepared[f"{column}__text_length"] = (
                    prepared[column].astype(str).str.len()
                )
                prepared[f"{column}__hash_bucket"] = prepared[column].map(
                    self._hash_bucket
                )
                prepared = prepared.drop(columns=[column])
                warnings.append(
                    f"High-cardinality text column {column!r} converted to length/hash features"
                )

        return prepared, warnings

    def assess_quality(self, df: pd.DataFrame) -> DataQualityReport:
        if df is None or df.empty:
            return DataQualityReport(
                0, 0, 1.0, 0.0, 0, [], 0.0, ["Source returned no rows"]
            )

        rows, columns = df.shape
        cells = rows * columns
        missing = float(df.isna().sum().sum() / cells) if cells else 0.0
        try:
            duplicates = int(df.duplicated().sum())
        except TypeError:
            duplicates = int(df.map(_json_string).duplicated().sum())
        duplicate_rate = float(duplicates / rows) if rows else 0.0
        empty_columns = int(df.isna().all(axis=0).sum())

        high_cardinality = []
        for column in df.columns:
            if rows and df[column].dtype == object:
                try:
                    unique_count = df[column].nunique(dropna=True)
                except TypeError:
                    unique_count = df[column].map(_json_string).nunique(dropna=True)
                if unique_count / rows > 0.8:
                    high_cardinality.append(str(column))

        warnings = []
        if missing > 0.2:
            warnings.append(f"High missing-value rate: {missing:.1%}")
        if duplicate_rate > 0.2:
            warnings.append(f"High duplicate-row rate: {duplicate_rate:.1%}")
        if empty_columns:
            warnings.append(f"{empty_columns} completely empty columns detected")

        score = max(
            0.0,
            min(
                1.0,
                1.0
                - min(0.45, missing * 0.9)
                - min(0.25, duplicate_rate * 0.5)
                - min(0.2, (empty_columns / max(columns, 1)) * 0.5),
            ),
        )
        return DataQualityReport(
            rows,
            columns,
            missing,
            duplicate_rate,
            empty_columns,
            high_cardinality,
            score,
            warnings,
        )

    @staticmethod
    def _hash_bucket(value: Any, buckets: int = 1024) -> int:
        return (
            int(hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:12], 16)
            % buckets
        )

    @staticmethod
    def _try_compress(
        data: np.ndarray, warnings: List[str]
    ) -> Optional[Dict[str, Any]]:
        try:
            from pythia_mining.pulvini import PHIFoldingCompressor

            compressor = PHIFoldingCompressor(compression_target=0.5)
            compressor.compress(data)
            return {
                "ratio": getattr(compressor, "compression_ratio", None),
                "fold_depth": getattr(compressor, "fold_depth", None),
                "error_bound": getattr(compressor, "error_bound", None),
            }
        except Exception as exc:
            warnings.append(f"PULVINI compression unavailable or failed: {exc}")
            return None


def create_default_ingestion_service() -> DataIngestionService:
    return DataIngestionService()
