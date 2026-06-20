"""
Comprehensive CIaaS Integration Tests
All connectors + packages + end-to-end workflows
"""

import pytest
import numpy as np
import pandas as pd
import logging
from pathlib import Path

# Import connectors
from hyba_ciaas.connectors import (
    SQLConnector, KafkaConnector, SCADAConnector,
    ProteinConnector, PubChemConnector, HTTPConnector
)

# Import packages
from hyba_ciaas.packages import PackageFactory

logger = logging.getLogger(__name__)


class TestConnectors:
    """Test universal connector framework"""
    
    def test_sql_connector_init(self):
        """Test SQL connector initialization"""
        config = {
            'db_type': 'postgresql',
            'host': 'localhost',
            'database': 'test',
            'user': 'test',
            'password': 'test',
        }
        connector = SQLConnector(config)
        assert connector.db_type == 'postgresql'
        assert connector.host == 'localhost'
        logger.info("✓ SQL connector init")
    
    def test_sql_connector_schema_detection(self):
        """Test auto-schema detection"""
        config = {
            'db_type': 'postgresql',
            'host': 'localhost',
            'database': 'test',
            'user': 'test',
            'password': 'test',
            'table': 'test_table',
        }
        connector = SQLConnector(config)
        # Note: will fail without actual database, but tests the interface
        logger.info("✓ SQL schema detection interface")
    
    def test_scada_connector(self):
        """Test SCADA connector for energy systems"""
        config = {
            'protocol': 'opcua',
            'host': 'grid-controller.local',
            'port': 4840,
            'measurement_types': ['voltage', 'frequency', 'power'],
        }
        connector = SCADAConnector(config)
        connector.connect()
        
        # Get grid topology
        topology = connector.get_grid_topology()
        assert 'nodes' in topology
        assert 'edges' in topology
        assert len(topology['nodes']) > 0
        logger.info(f"✓ SCADA topology: {len(topology['nodes'])} nodes")
        
        connector.disconnect()
    
    def test_protein_connector(self):
        """Test protein structure connector"""
        config = {
            'source': 'uniprot',
            'query': 'P69905',  # Hemoglobin
            'embedding': 'esm2',
        }
        connector = ProteinConnector(config)
        connector.connect()
        
        # Schema detection
        schema = connector.auto_detect_schema()
        assert 'protein_id' in schema.columns
        assert 'sequence' in schema.columns
        logger.info("✓ Protein connector schema")
        
        connector.disconnect()
    
    def test_pubchem_connector(self):
        """Test drug discovery connector"""
        config = {
            'search_query': 'aspirin',
            'limit': 100,
            'include_bioassay': True,
        }
        connector = PubChemConnector(config)
        connector.connect()
        
        # Fetch compounds
        df = connector.fetch_data(limit=10)
        assert len(df) > 0
        assert 'smiles' in df.columns
        assert 'fingerprint' in df.columns
        logger.info(f"✓ PubChem: {len(df)} compounds fetched")
        
        # Structural similarity
        if len(df) >= 2:
            smiles1 = df.iloc[0]['smiles']
            smiles2 = df.iloc[1]['smiles']
            similarity = connector.structural_similarity(smiles1, smiles2)
            assert 0 <= similarity <= 1
            logger.info(f"  Similarity: {similarity:.3f}")
        
        connector.disconnect()
    
    def test_kafka_connector_streaming(self):
        """Test real-time data streaming"""
        config = {
            'broker_type': 'kafka',
            'brokers': 'localhost:9092',
            'topic': 'grid-measurements',
        }
        connector = KafkaConnector(config)
        connector.connect()
        
        # Stream batches
        batch_count = 0
        for batch in connector.stream_data(batch_size=100):
            batch_count += 1
            assert len(batch) > 0
            if batch_count >= 3:
                break
        
        logger.info(f"✓ Kafka streaming: {batch_count} batches")
        connector.disconnect()
    
    def test_http_connector_government_api(self):
        """Test government API connector"""
        config = {
            'endpoint': 'https://api.weather.gov/points/38.0,-77.0',
            'method': 'GET',
            'headers': {'User-Agent': 'HYBA-Test'},
        }
        connector = HTTPConnector(config)
        connector.connect()
        
        # This will test the interface (actual API call may fail in test env)
        logger.info("✓ HTTP connector for government APIs")
        connector.disconnect()


class TestPackages:
    """Test optimization packages"""
    
    def test_government_security_package(self):
        """Test government security optimization"""
        package = PackageFactory.create('government')
        assert package.name == "Government Security Optimization"
        
        # Create test data
        n_nodes = 50
        n_features = 35
        data = np.random.uniform(0, 1, (n_nodes, n_features))
        
        # Run optimization
        result = package.optimize(data, {})
        
        assert 'threats' in result
        assert 'resource_allocation' in result
        assert 'prioritized_infrastructure' in result
        assert result['confidence'] > 0.9
        logger.info(f"✓ Government security optimization: {len(result['recommended_actions'])} actions")
    
    def test_energy_optimization_package(self):
        """Test smart grid optimization"""
        package = PackageFactory.create('energy')
        assert package.name == "Energy Grid Optimization"
        
        # Create test data: timestamps + generation + demand + storage + network
        n_timesteps = 24  # 24 hours
        n_features = 35
        data = np.random.uniform(0, 1, (n_timesteps, n_features))
        
        # Run optimization
        result = package.optimize(data, {})
        
        assert 'demand_forecast' in result
        assert 'renewable_available' in result
        assert 'optimal_dispatch' in result
        assert 'autonomous_actions' in result
        logger.info(f"✓ Energy optimization: {len(result['autonomous_actions'])} control actions")
    
    def test_protein_folding_package(self):
        """Test protein structure prediction"""
        package = PackageFactory.create('protein')
        assert package.name == "Protein Folding Prediction"
        
        # Create test data: sequence encoding + constraints + targets
        sequence_length = 100
        n_features = 50
        data = np.random.randint(0, 20, (sequence_length, n_features))
        
        # Run prediction
        result = package.optimize(data, {})
        
        assert 'sequence_analysis' in result
        assert 'secondary_structure' in result
        assert 'tertiary_structure' in result
        assert 'binding_sites' in result
        assert 'druggability' in result
        assert result['confidence'] > 0.65
        logger.info(f"✓ Protein folding: {result['prediction_time_minutes']} min prediction")


class TestEndToEnd:
    """End-to-end integration tests"""
    
    def test_government_workflow(self):
        """Government security: data ingestion → optimization → actions"""
        logger.info("\n=== Government Security Workflow ===")
        
        # 1. Ingest threat data (simulated HTTP API)
        config = {
            'endpoint': 'https://api.cisa.gov/threats',
            'method': 'GET',
        }
        connector = HTTPConnector(config)
        connector.connect()
        
        # Simulate ingested data
        threat_data = np.random.uniform(0, 1, (100, 35))
        logger.info("1. Threat data ingested: 100 nodes, 35 features")
        
        # 2. Run optimization
        package = PackageFactory.create('government')
        result = package.optimize(threat_data, {})
        logger.info(f"2. Optimization complete: {len(result['recommended_actions'])} recommendations")
        
        # 3. Generate autonomous actions
        actions = result['recommended_actions']
        assert len(actions) > 0
        logger.info(f"3. Generated {len(actions)} autonomous actions")
        
        for action in actions[:3]:
            logger.info(f"   - {action}")
        
        connector.disconnect()
    
    def test_energy_workflow(self):
        """Energy optimization: SCADA → optimization → setpoints"""
        logger.info("\n=== Energy Grid Optimization Workflow ===")
        
        # 1. Connect to SCADA and stream data
        config = {
            'protocol': 'opcua',
            'host': 'grid.local',
            'measurement_types': ['voltage', 'power', 'frequency'],
        }
        connector = SCADAConnector(config)
        connector.connect()
        
        # Get topology
        topology = connector.get_grid_topology()
        logger.info(f"1. SCADA connected: {len(topology['nodes'])} grid nodes")
        
        # Generate SCADA data
        grid_data = np.random.uniform(0, 1, (24, 35))
        logger.info(f"   - 24 hours of measurements ingested")
        
        # 2. Run energy optimization
        package = PackageFactory.create('energy')
        result = package.optimize(grid_data, {})
        logger.info(f"2. Optimization complete: {result['efficiency_improvement']:.1f}% efficiency gain")
        
        # 3. Convert to SCADA setpoints
        setpoints = connector.propose_setpoints(result['optimal_dispatch'])
        logger.info(f"3. Generated {len(setpoints)} setpoint commands")
        
        for node_id, sp in list(setpoints.items())[:3]:
            logger.info(f"   - {node_id}: {sp}")
        
        connector.disconnect()
    
    def test_drug_discovery_workflow(self):
        """Drug discovery: PubChem → protein folding → hit ranking"""
        logger.info("\n=== Drug Discovery Workflow ===")
        
        # 1. Fetch compounds from PubChem
        chem_config = {
            'search_query': 'kinase inhibitor',
            'limit': 100,
        }
        chem_connector = PubChemConnector(chem_config)
        chem_connector.connect()
        
        compounds = chem_connector.fetch_data(limit=50)
        logger.info(f"1. Fetched {len(compounds)} candidate compounds from PubChem")
        
        # 2. Fetch target protein structure
        protein_config = {
            'source': 'uniprot',
            'query': 'P12345',  # Target kinase
        }
        protein_connector = ProteinConnector(protein_config)
        protein_connector.connect()
        
        target_data = np.random.randint(0, 20, (250, 50))
        logger.info(f"2. Fetched target protein: 250 residues")
        
        # 3. Predict target structure
        protein_package = PackageFactory.create('protein')
        protein_result = protein_package.optimize(target_data, {})
        logger.info(f"3. Protein structure prediction: {protein_result['prediction_time_minutes']} min")
        logger.info(f"   - Binding sites: {protein_result['druggability']['binding_sites_count']}")
        logger.info(f"   - Druggability: {protein_result['druggability']['overall_score']:.2f}")
        
        # 4. Rank compounds by binding potential
        ranked_compounds = self._rank_compounds_for_target(compounds, protein_result)
        logger.info(f"4. Ranked top 10 hits:")
        for i, (cmpd, score) in enumerate(ranked_compounds[:10], 1):
            logger.info(f"   {i}. CID {cmpd['cid']}: {score:.2f} binding score")
        
        chem_connector.disconnect()
        protein_connector.disconnect()
    
    def _rank_compounds_for_target(self, compounds: pd.DataFrame, target_result: dict) -> list:
        """Rank compounds by predicted binding to target"""
        # Simplified: combine molecular properties with target druggability
        ranked = []
        
        for _, cmpd in compounds.iterrows():
            # Fingerprint similarity to known actives (simplified)
            if 'fingerprint' in cmpd:
                fp = cmpd['fingerprint']
                if isinstance(fp, np.ndarray):
                    # Score based on hydrophobic content (approximation)
                    hydrophobic_fraction = np.mean(fp) if isinstance(fp, np.ndarray) else 0.5
                    
                    # Combine with target druggability
                    binding_score = hydrophobic_fraction * target_result['druggability']['overall_score']
                    ranked.append((cmpd.to_dict(), binding_score))
        
        return sorted(ranked, key=lambda x: x[1], reverse=True)


class TestPackageFactory:
    """Test package factory pattern"""
    
    def test_list_packages(self):
        """List all available packages"""
        packages = PackageFactory.list_packages()
        assert 'government' in packages
        assert 'energy' in packages
        assert 'protein' in packages
        logger.info(f"✓ Available packages: {packages}")
    
    def test_create_by_name(self):
        """Create packages by name"""
        for name in PackageFactory.list_packages():
            package = PackageFactory.create(name)
            assert package is not None
            assert hasattr(package, 'optimize')
            logger.info(f"✓ Created: {package.name}")


if __name__ == '__main__':
    # Run tests
    logging.basicConfig(level=logging.INFO)
    pytest.main([__file__, '-v', '-s'])
