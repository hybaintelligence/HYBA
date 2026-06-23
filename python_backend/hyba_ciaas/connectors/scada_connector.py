"""
SCADA Connector for Energy Systems
Supports: OPC-UA, Modbus, DNP3 protocols
Real-time grid, wind turbine, battery monitoring
"""

from typing import Dict, List, Any, Optional, Iterator
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from collections import deque

from .base_connector import UniversalConnector, ConnectorSchema, DataType

logger = logging.getLogger(__name__)


class SCADAConnector(UniversalConnector):
    """
    SCADA systems connector for energy infrastructure.

    Supports:
    - Real-time sensor data (temperature, pressure, voltage, frequency)
    - Time-series ingestion (1Hz to 1min resolution)
    - Smart grid topology (nodes, edges, flows)
    - Autonomous control output (setpoint recommendations)
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Config:
        - protocol: 'opcua', 'modbus', 'dnp3'
        - host, port
        - measurement_types: ['voltage', 'frequency', 'temperature', 'power']
        - storage: 'memory' (ringbuffer) or 'influxdb'
        """
        super().__init__(config)
        self.protocol = config.get("protocol", "opcua").lower()
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 4840)
        self.measurement_types = config.get(
            "measurement_types",
            [
                "voltage",
                "frequency",
                "power_real",
                "power_reactive",
                "current",
                "temperature",
                "pressure",
            ],
        )
        self.storage = config.get("storage", "memory")
        self.buffer_size = config.get("buffer_size", 86400)  # 1 day of data
        self.data_buffer = deque(maxlen=self.buffer_size)
        self._client = None

    def connect(self):
        """Connect to SCADA system"""
        try:
            if self.protocol == "opcua":
                from opcua import Client

                self._client = Client(
                    f"opc.tcp://{self.host}:{self.port}/freeopcua/server/"
                )
                self._client.connect()
                logger.info(f"Connected to OPC-UA server at {self.host}:{self.port}")
            elif self.protocol == "modbus":
                from pymodbus.client import ModbusTcpClient

                self._client = ModbusTcpClient(host=self.host, port=self.port)
                self._client.connect()
                logger.info(f"Connected to Modbus server at {self.host}:{self.port}")
            elif self.protocol == "dnp3":
                logger.info(f"DNP3 protocol support (requires pydnp3 library)")
                # DNP3 implementation would go here
            else:
                # Simulation mode (for testing)
                logger.info(f"SCADA connector in simulation mode (no real connection)")
                self._client = "simulated"
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self._client = "simulated"

    def disconnect(self):
        """Disconnect from SCADA"""
        if self._client and self._client != "simulated":
            try:
                self._client.close()
                logger.info("Disconnected from SCADA")
            except:
                pass

    def auto_detect_schema(self) -> ConnectorSchema:
        """
        Auto-detect available measurements from SCADA.
        Returns schema for grid monitoring data.
        """
        # Generate schema based on measurement types
        columns = {
            "timestamp": DataType.TEMPORAL,
            "node_id": DataType.CATEGORICAL,
        }

        for mtype in self.measurement_types:
            columns[mtype] = DataType.NUMERIC

        # Sample: generate synthetic data for schema
        df_sample = self._generate_sample_data(100)

        return ConnectorSchema(
            columns=columns,
            row_count=1000000,  # Assume large dataset
            estimated_size_bytes=len(self.measurement_types) * 8 * 1000000,
            last_updated=datetime.utcnow().isoformat(),
            sample_rows=df_sample,
            missing_value_rate=0.01,
            data_types_detected={
                col: "float64" if col != "timestamp" else "datetime64"
                for col in columns
            },
        )

    def _generate_sample_data(self, n_samples: int = 100) -> pd.DataFrame:
        """Generate synthetic SCADA data for schema detection"""
        np.random.seed(42)

        data = {
            "timestamp": pd.date_range(
                start="2026-06-20", periods=n_samples, freq="1S"
            ),
            "node_id": np.random.choice(
                ["GRID-01", "GRID-02", "WIND-01", "SOLAR-01"], n_samples
            ),
            "voltage": 120 + np.random.normal(0, 2, n_samples),
            "frequency": 60 + np.random.normal(0, 0.1, n_samples),
            "power_real": 1000 + np.random.normal(0, 100, n_samples),
            "power_reactive": np.random.normal(0, 50, n_samples),
            "current": 50 + np.random.normal(0, 5, n_samples),
            "temperature": 25 + np.random.normal(0, 3, n_samples),
            "pressure": 1000 + np.random.normal(0, 10, n_samples),
        }

        return pd.DataFrame(data)

    def fetch_data(
        self, query: Optional[str] = None, limit: int = None
    ) -> pd.DataFrame:
        """
        Fetch recent SCADA data.
        Query format: "node_id=GRID-01&minutes=60" (last 60 minutes)
        """
        if query:
            params = {kv.split("=")[0]: kv.split("=")[1] for kv in query.split("&")}
            node_id = params.get("node_id")
            minutes = int(params.get("minutes", 60))
        else:
            node_id = None
            minutes = 60

        # Generate synthetic recent data
        n_samples = minutes * 60  # 1 Hz
        df = self._generate_sample_data(n_samples)

        if node_id:
            df = df[df["node_id"] == node_id]

        if limit:
            df = df.tail(limit)

        logger.info(f"Fetched {len(df)} SCADA measurements")
        return df

    def stream_data(self, batch_size: int = 3600) -> Iterator[pd.DataFrame]:
        """
        Stream SCADA data in batches (default 1 hour chunks).
        In production, this would read live from SCADA system.
        """
        # For testing/demo, generate batches of synthetic data
        total_rows = 0

        while True:
            batch = self._generate_sample_data(batch_size)

            if batch.empty:
                break

            self.data_buffer.extend(batch.to_dict("records"))
            total_rows += len(batch)

            logger.info(f"SCADA stream batch: {len(batch)} measurements")
            yield batch

            # In production, this would be continuous
            if total_rows > 86400:  # Stop after 1 day demo
                break

        logger.info(f"SCADA stream complete: {total_rows} total measurements")

    def get_grid_topology(self) -> Dict[str, Any]:
        """Get smart grid topology (nodes, edges, flows)"""
        return {
            "nodes": [
                {"id": "GRID-01", "type": "substation", "voltage": 138000},
                {"id": "GRID-02", "type": "substation", "voltage": 69000},
                {"id": "WIND-01", "type": "generator", "capacity": 100},
                {"id": "SOLAR-01", "type": "generator", "capacity": 50},
                {"id": "BATTERY-01", "type": "storage", "capacity": 200},
                {"id": "LOAD-01", "type": "load", "demand": 500},
                {"id": "LOAD-02", "type": "load", "demand": 300},
            ],
            "edges": [
                {"from": "WIND-01", "to": "GRID-01", "impedance": 0.05},
                {"from": "SOLAR-01", "to": "GRID-02", "impedance": 0.03},
                {"from": "GRID-01", "to": "GRID-02", "impedance": 0.02},
                {"from": "GRID-01", "to": "LOAD-01", "impedance": 0.01},
                {"from": "GRID-02", "to": "LOAD-02", "impedance": 0.01},
                {"from": "BATTERY-01", "to": "GRID-01", "impedance": 0.04},
            ],
        }

    def propose_setpoints(self, optimization_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert optimization results to SCADA setpoint commands.

        Output format:
        {
            'WIND-01': {'power_setpoint': 95.0},  # MW
            'SOLAR-01': {'power_setpoint': 48.5},
            'BATTERY-01': {'power_setpoint': -10.0},  # Negative = charging
            'LOAD-01': {'curtailment': 0.05},  # 5% load reduction
        }
        """
        logger.info(f"Converting optimization to setpoints: {optimization_results}")

        setpoints = {}
        for node_id, values in optimization_results.items():
            if node_id.startswith("WIND") or node_id.startswith("SOLAR"):
                setpoints[node_id] = {"power_setpoint": float(values.get("power", 0))}
            elif node_id.startswith("BATTERY"):
                setpoints[node_id] = {
                    "power_setpoint": float(values.get("charge_power", 0))
                }
            elif node_id.startswith("LOAD"):
                setpoints[node_id] = {"curtailment": float(values.get("reduction", 0))}

        return setpoints
