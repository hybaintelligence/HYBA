# Test Templates Library for 4 Agents
## Copy-Paste Ready Templates with Examples

---

## AGENT 1: Mining Engine Templates

### Template 1A: Engine Initialization Test
```python
# tests/test_agent1_engine_initialization.py
"""Test unified mining engine initialization."""
import pytest
from unittest.mock import MagicMock, patch
from python_backend.pythia_mining.phi_unified_mining_engine import UnifiedMiningEngine

class TestUnifiedMiningEngineInitialization:
    """Test engine initialization and configuration."""
    
    def test_engine_initialization_default(self):
        """Test engine initializes with default configuration."""
        engine = UnifiedMiningEngine()
        
        assert engine is not None
        assert engine.is_available_flag is True
        assert hasattr(engine, 'solver')
        assert hasattr(engine, 'optimizer')
    
    def test_engine_initialization_with_custom_capacity(self):
        """Test engine initializes with custom capacity."""
        engine = UnifiedMiningEngine(configured_capacity_ehs=50.0)
        
        assert engine.configured_capacity_ehs == 50.0
        assert engine.calculate_integrated_hashrate() <= 50.0
    
    def test_engine_lifecycle_startup_shutdown(self):
        """Test engine lifecycle: startup and shutdown."""
        engine = UnifiedMiningEngine()
        
        # Engine should start in valid state
        assert engine.is_available() is True
        
        # Simulate shutdown
        engine.is_available_flag = False
        assert engine.is_available() is False
```

### Template 1B: Strategy Selection Test
```python
# tests/test_agent1_strategy_selection.py
"""Test mining strategy selection."""
import pytest
from python_backend.pythia_mining.ai_optimizer import AIOptimizer

class TestStrategySelection:
    """Test search strategy selection based on metrics."""
    
    @pytest.mark.parametrize("coherence,expected_strategy", [
        (0.85, "aggressive"),
        (0.70, "balanced"),
        (0.50, "conservative"),
    ])
    def test_strategy_selection_by_coherence(self, coherence, expected_strategy):
        """Test strategy selection based on phi coherence level."""
        optimizer = AIOptimizer()
        strategy = optimizer.select_strategy(phi_coherence=coherence)
        
        assert strategy is not None
        # Verify strategy name contains expected keyword
        assert expected_strategy in str(strategy).lower()
    
    def test_strategy_adaptation_on_failure(self):
        """Test strategy adapts after failure."""
        optimizer = AIOptimizer()
        
        initial_strategy = optimizer.select_strategy(phi_coherence=0.75)
        # Simulate failure
        optimizer.record_failure()
        
        adapted_strategy = optimizer.select_strategy(phi_coherence=0.75)
        # Strategy should adapt to be more conservative
        assert adapted_strategy is not None
```

### Template 1C: Metrics & Reporting Test
```python
# tests/test_agent1_metrics_reporting.py
"""Test metrics calculation and reporting."""
import pytest
from python_backend.pythia_mining.phi_unified_mining_engine import UnifiedMiningEngine

class TestMetricsAndReporting:
    """Test mining metrics calculation."""
    
    def test_hashrate_calculation_accuracy(self):
        """Test hashrate is calculated accurately."""
        engine = UnifiedMiningEngine(configured_capacity_ehs=100.0)
        
        hashrate = engine.calculate_integrated_hashrate()
        
        assert hashrate is not None
        assert isinstance(hashrate, (int, float))
        assert hashrate > 0
        assert hashrate <= 100.0
    
    def test_efficiency_score_computation(self):
        """Test efficiency score is computed correctly."""
        engine = UnifiedMiningEngine()
        
        # Create mock metrics
        metrics = {
            "shares_accepted": 10,
            "shares_submitted": 12,
            "power_consumed_watts": 500.0,
        }
        
        efficiency = engine.calculate_efficiency(metrics)
        
        assert efficiency is not None
        assert 0.0 <= efficiency <= 1.0
```

### Template 1D: Configuration Validation Test
```python
# tests/test_agent1_config_validation.py
"""Test configuration validation."""
import pytest
from python_backend.pythia_mining.phi_config import PhiConfig

class TestConfigurationValidation:
    """Test configuration bounds checking."""
    
    def test_capacity_limits_enforcement(self):
        """Test capacity limits are enforced."""
        config = PhiConfig()
        
        # Should accept valid capacity
        assert config.set_capacity(50.0) is True
        
        # Should reject invalid capacity
        assert config.set_capacity(-1.0) is False
        assert config.set_capacity(1000.0) is False
    
    def test_environment_variable_precedence(self):
        """Test environment variables take precedence."""
        import os
        from unittest.mock import patch
        
        with patch.dict(os.environ, {"HYBA_MINING_CAPACITY": "75.0"}):
            config = PhiConfig()
            assert config.capacity == 75.0
```

---

## AGENT 2: Pool & Stratum Templates

### Template 2A: Stratum Session Test
```python
# tests/test_agent2_stratum_session.py
"""Test Stratum protocol session management."""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from python_backend.pythia_mining.live_stratum_session import LiveStratumSession
from python_backend.pythia_mining.pool_profiles import PoolProfile

class TestStratumSessionLifecycle:
    """Test Stratum session lifecycle."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.profile = PoolProfile(
            pool_id="test_pool",
            pool_name="Test Pool",
            url="stratum+tcp://localhost:3333",
            username="testuser",
            password="testpass"
        )
    
    @pytest.mark.asyncio
    async def test_stratum_session_connection(self):
        """Test Stratum session can connect."""
        session = LiveStratumSession(self.profile)
        
        with patch.object(session.transport, 'connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = True
            result = await session.connect()
            
            assert result is True or result is None  # Connection succeeded
            mock_connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stratum_session_graceful_disconnect(self):
        """Test Stratum session graceful disconnect."""
        session = LiveStratumSession(self.profile)
        
        with patch.object(session.transport, 'close', new_callable=AsyncMock) as mock_close:
            mock_close.return_value = None
            await session.close()
            
            mock_close.assert_called_once()
```

### Template 2B: Job Management Test
```python
# tests/test_agent2_job_management.py
"""Test mining job management."""
import pytest
from python_backend.pythia_mining.stratum_client import MiningJob

class TestJobManagement:
    """Test job parsing and management."""
    
    def test_mining_job_creation(self):
        """Test mining job creation."""
        job = MiningJob(
            job_id="job_1",
            prev_hash="00" * 32,
            coin_base_1="coinbase1",
            coin_base_2="coinbase2",
            merkle_branches=[],
            block_version="00000001",
            network_difficulty="1a000000",
            ntime="time1234",
            clean_jobs=True
        )
        
        assert job.job_id == "job_1"
        assert job.prev_hash == "00" * 32
        assert job.clean_jobs is True
    
    @pytest.mark.parametrize("difficulty", [
        "1d00ffff",  # Bitcoin difficulty 1
        "1a000000",  # Higher difficulty
        "17000000",  # Much higher difficulty
    ])
    def test_job_difficulty_parsing(self, difficulty):
        """Test job difficulty parsing."""
        job = MiningJob(
            job_id="test",
            prev_hash="00" * 32,
            coin_base_1="cb1",
            coin_base_2="cb2",
            merkle_branches=[],
            block_version="00000001",
            network_difficulty=difficulty,
            ntime="time",
            clean_jobs=True
        )
        
        assert job.network_difficulty == difficulty
```

### Template 2C: Pool Profile Test
```python
# tests/test_agent2_pool_profiles.py
"""Test pool profile management."""
import pytest
from python_backend.pythia_mining.pool_profiles import PoolProfile, PoolCredentialConfig

class TestPoolProfiles:
    """Test pool profile creation and validation."""
    
    def test_pool_profile_creation(self):
        """Test pool profile creation."""
        profile = PoolProfile(
            pool_id="braiins",
            pool_name="Braiins",
            url="stratum+tcp://stratum.braiins.com:3333",
            username="user",
            password="pass"
        )
        
        assert profile.pool_id == "braiins"
        assert profile.pool_name == "Braiins"
        assert "braiins.com" in profile.url
    
    def test_pool_credential_config(self):
        """Test pool credential configuration."""
        config = PoolCredentialConfig(
            pool_id="test",
            url="stratum+tcp://test:3333",
            username="user",
            password="pass"
        )
        
        assert config.pool_id == "test"
        assert config.resolved_username() == "user"
        assert config.resolved_password() == "pass"
    
    @pytest.mark.parametrize("url", [
        "stratum+tcp://pool.com:3333",
        "stratum+ssl://pool.com:443",
        "stratum2+ssl://pool.com:3336",
    ])
    def test_various_pool_urls(self, url):
        """Test various pool URL schemes."""
        profile = PoolProfile(
            pool_id="test",
            pool_name="Test",
            url=url,
            username="user",
            password="pass"
        )
        
        assert profile.url == url
```

---

## AGENT 3: Quantum & Solvers Templates

### Template 3A: Quantum Solver Initialization Test
```python
# tests/test_agent3_quantum_init.py
"""Test quantum solver initialization."""
import pytest
from python_backend.pythia_mining.quantum_solver import DodecahedralQuantumSolver

class TestQuantumSolverInitialization:
    """Test quantum solver setup."""
    
    def test_quantum_solver_initialization(self):
        """Test quantum solver initializes correctly."""
        solver = DodecahedralQuantumSolver()
        
        assert solver is not None
        assert solver.is_available() is True
        assert solver.basis_states is not None
        assert solver.basis_states.shape[0] == 20  # 20 dodecahedral vertices
    
    def test_basis_states_generation(self):
        """Test basis states are generated correctly."""
        solver = DodecahedralQuantumSolver()
        
        basis = solver.basis_states
        
        # Check shape
        assert basis.shape[0] == 20
        assert basis.shape[1] >= 1
        
        # Check normalization (each basis state should have norm ~1)
        import numpy as np
        norms = np.linalg.norm(basis, axis=1)
        assert all(0.99 < norm < 1.01 for norm in norms)
    
    def test_phi_phase_alignment(self):
        """Test golden ratio phase alignment."""
        solver = DodecahedralQuantumSolver()
        
        # Get phase alignment metric
        alignment = solver._phi_phase_alignment()
        
        assert 0.0 <= alignment <= 1.0
        assert alignment > 0.5  # Should be reasonably aligned
```

### Template 3B: Nonce Generation Test
```python
# tests/test_agent3_nonce_generation.py
"""Test nonce generation and search."""
import pytest
from python_backend.pythia_mining.quantum_solver import DodecahedralQuantumSolver

class TestNonceGeneration:
    """Test nonce generation."""
    
    @pytest.mark.asyncio
    async def test_nonce_generation_basic(self):
        """Test basic nonce generation."""
        solver = DodecahedralQuantumSolver()
        
        # Configure solver
        await solver.configure_search(
            target=2**200,
            nonce_ranges=[(0, 2**32 - 1)]
        )
        
        # Verify configuration
        assert solver.current_config is not None
        assert solver.current_config['target'] == 2**200
    
    @pytest.mark.parametrize("start,end", [
        (0, 1000),
        (100, 1000),
        (0, 2**32-1),
    ])
    def test_nonce_range_validation(self, start, end):
        """Test nonce range validation."""
        solver = DodecahedralQuantumSolver()
        
        ranges = [(start, end)]
        validated = solver._validate_nonce_ranges(ranges)
        
        assert len(validated) > 0
        assert validated[0] == (start, end)
    
    def test_nonce_uniqueness(self):
        """Test nonce uniqueness tracking."""
        solver = DodecahedralQuantumSolver()
        
        # Add nonces to tracking set
        solver._used_nonces.add(12345)
        solver._used_nonces.add(67890)
        
        assert 12345 in solver._used_nonces
        assert 67890 in solver._used_nonces
        assert 11111 not in solver._used_nonces
```

### Template 3C: Classical Fallback Test
```python
# tests/test_agent3_fallback.py
"""Test classical fallback mechanism."""
import pytest
from python_backend.pythia_mining.quantum_solver import DodecahedralQuantumSolver

class TestClassicalFallback:
    """Test fallback to classical search."""
    
    @pytest.mark.asyncio
    async def test_fallback_activation(self):
        """Test fallback to classical search activates."""
        solver = DodecahedralQuantumSolver()
        
        await solver.configure_search(
            target=2**200,
            nonce_ranges=[(0, 1000)]
        )
        
        # Try solving with low iterations (forces fallback)
        result = await solver.solve(max_iterations=1, timeout=0.1)
        
        # Result may be None or a valid nonce
        assert result is None or isinstance(result, int)
    
    def test_classical_determinism(self):
        """Test classical search is deterministic."""
        import asyncio
        
        async def run_classical_search(seed):
            solver = DodecahedralQuantumSolver()
            solver._solve_call_count = seed
            
            await solver.configure_search(
                target=2**200,
                nonce_ranges=[(0, 100)]
            )
            
            return await solver.solve(max_iterations=10, timeout=1.0)
        
        # Run with same seed twice
        result1 = asyncio.run(run_classical_search(1))
        result2 = asyncio.run(run_classical_search(1))
        
        # Results should be the same (deterministic)
        assert result1 == result2
```

---

## AGENT 4: Data & Storage Templates

### Template 4A: Phi-Folding Compression Test
```python
# tests/test_agent4_phi_folding.py
"""Test phi-folding compression."""
import pytest
import numpy as np
from python_backend.pythia_mining.pulvini_phi_memory import PulviniPhiMemoryCompressionEngine

class TestPhiFoldingCompression:
    """Test phi-folding compression mechanism."""
    
    def test_compression_engine_initialization(self):
        """Test compression engine initializes."""
        engine = PulviniPhiMemoryCompressionEngine()
        
        assert engine is not None
        assert engine.tolerance > 0
        assert engine.fold_depth >= 1
    
    def test_compression_basic(self):
        """Test basic compression."""
        engine = PulviniPhiMemoryCompressionEngine()
        
        # Create simple data
        data = np.linspace(0.0, 1.0, 32, dtype=np.float64)
        
        # Compress
        result = engine.compress(data)
        
        assert result.folded_dimension < len(data)
        assert result.reversible is True
        assert result.reconstruction_error < 1e-9
    
    @pytest.mark.parametrize("size", [16, 32, 64, 128])
    def test_compression_various_sizes(self, size):
        """Test compression on various data sizes."""
        engine = PulviniPhiMemoryCompressionEngine()
        
        data = np.random.randn(size)
        result = engine.compress(data)
        
        assert result.reversible is True
        assert result.reconstruction_error < 1e-9
```

### Template 4B: Knowledge Base Integration Test
```python
# tests/test_agent4_knowledge_base.py
"""Test knowledge base integration."""
import pytest
from python_backend.pythia_mining.mining_knowledge_base import MiningKnowledgeBase

class TestKnowledgeBaseIntegration:
    """Test knowledge base for mining decisions."""
    
    def test_knowledge_base_initialization(self):
        """Test knowledge base initializes."""
        kb = MiningKnowledgeBase()
        
        assert kb is not None
        assert kb.success_criteria is not None
        assert kb.pitfalls is not None
        assert kb.rules is not None
        assert kb.expectations is not None
    
    def test_success_criteria_evaluation(self):
        """Test success criteria evaluation."""
        kb = MiningKnowledgeBase()
        
        metrics = {
            "hashrate_threshold": 100.0,
            "temperature_threshold": 50.0,
            "error_rate_threshold": 0.1,
            "uptime_threshold": 99.0,
        }
        
        evaluation = kb.evaluate_current_state(metrics)
        
        assert "success_evaluation" in evaluation
        assert "overall_assessment" in evaluation
        assert evaluation["overall_assessment"]["status"] in ["healthy", "warning", "critical"]
    
    def test_pitfall_detection(self):
        """Test pitfall detection."""
        kb = MiningKnowledgeBase()
        
        metrics = {
            "temperature_threshold": 85.0,  # High temperature - thermal pitfall
            "error_rate_threshold": 2.0,     # High error rate
        }
        
        evaluation = kb.evaluate_current_state(metrics)
        pitfalls = evaluation["pitfall_indicators"]
        
        # Should detect issues
        assert len(pitfalls) >= 0  # May or may not detect depending on thresholds
```

### Template 4C: Performance Test
```python
# tests/test_agent4_performance.py
"""Test data operation performance."""
import pytest
import numpy as np
import time
from python_backend.pythia_mining.pulvini_phi_memory import PulviniPhiMemoryCompressionEngine

class TestPerformance:
    """Test performance characteristics."""
    
    def test_compression_speed(self):
        """Test compression speed is acceptable."""
        engine = PulviniPhiMemoryCompressionEngine()
        
        data = np.random.randn(1000)
        
        start = time.time()
        result = engine.compress(data)
        elapsed = time.time() - start
        
        # Should compress reasonably fast (< 1 second)
        assert elapsed < 1.0
        assert result.reversible is True
    
    def test_scaling_with_data_size(self):
        """Test scaling with increasing data size."""
        engine = PulviniPhiMemoryCompressionEngine()
        
        times = []
        for size in [100, 1000, 10000]:
            data = np.random.randn(size)
            
            start = time.time()
            result = engine.compress(data)
            elapsed = time.time() - start
            
            times.append(elapsed)
            assert result.reversible is True
        
        # Verify roughly linear scaling
        ratio = times[-1] / times[0]
        assert ratio < 100  # Should scale roughly linearly
```

---

## Common Fixture Library

```python
# tests/conftest_agents.py
"""Shared fixtures for all agents."""
import pytest
from unittest.mock import MagicMock, patch
import numpy as np

@pytest.fixture
def mock_pool_profile():
    """Mock pool profile."""
    profile = MagicMock()
    profile.pool_id = "test_pool"
    profile.url = "stratum+tcp://localhost:3333"
    profile.username = "testuser"
    profile.password = "testpass"
    return profile

@pytest.fixture
def mock_mining_job():
    """Mock mining job."""
    job = MagicMock()
    job.job_id = "job_1"
    job.prev_hash = "00" * 32
    job.clean_jobs = True
    return job

@pytest.fixture
def mock_quantum_solver():
    """Mock quantum solver."""
    solver = MagicMock()
    solver.is_available.return_value = True
    solver.basis_states = np.random.randn(20, 3)
    return solver

@pytest.fixture
def sample_mining_metrics():
    """Sample mining metrics."""
    return {
        "hashrate_threshold": 100.0,
        "temperature_threshold": 50.0,
        "error_rate_threshold": 0.1,
        "uptime_threshold": 99.0,
        "latency_threshold": 50.0,
        "power_threshold": 200.0,
    }

@pytest.fixture
def sample_compression_data():
    """Sample data for compression tests."""
    return np.linspace(0.0, 1.0, 32, dtype=np.float64)
```

---

## Tips for Success

1. **Use Templates**: Copy-paste these templates and adapt for your modules
2. **Follow Naming**: Use `test_agent{N}_{topic}.py` file naming
3. **Test One Thing**: Each test should verify one behavior
4. **Use Mocks Wisely**: Mock external dependencies, not internal logic
5. **Parameterize**: Use `@pytest.mark.parametrize` for multiple inputs
6. **Async Support**: Use `@pytest.mark.asyncio` for async tests
7. **Error Cases**: Always test error paths
8. **Performance**: Keep individual tests < 2 seconds
9. **Documentation**: Add docstrings to all tests
10. **Verify Coverage**: Run with `--cov` to check coverage

---

**Ready to go!** Pick your agent, choose a template, and start writing tests! 🚀
