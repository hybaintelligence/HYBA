# Quick Start Guide for Cloud Agents
## Coverage Push: 30% → 80%+ (4 Parallel Agents)

---

## 🎯 Your Assignment

| Agent | Module Focus | Test File Prefix | Est. Tests | Lead |
|-------|-------------|------------------|-----------|------|
| **1** | `phi_unified_mining_engine.py` | `test_agent1_` | 45-50 | Engine & Orchestration |
| **2** | `live_stratum_session.py` | `test_agent2_` | 40-45 | Pool Integration |
| **3** | `quantum_solver.py` | `test_agent3_` | 35-40 | Quantum & Math |
| **4** | `pulvini_phi_memory.py` | `test_agent4_` | 30-35 | Data & Compression |

---

## 📋 Step 1: Clone & Setup (2 min)

```bash
# Navigate to project
cd /Users/demouser/Desktop/HYBA_FULLSTACK

# Ensure environment is clean
python -m pytest --collect-only tests/ 2>/dev/null | grep "test session starts"

# Check Python version
python --version  # Should be 3.12+

# Install any missing test deps
pip install pytest pytest-asyncio hypothesis -q
```

---

## 📝 Step 2: Find Your Test Groups

```bash
# View the detailed test plan
cat TEST_COVERAGE_PLAN_4_AGENTS.md | grep "## AGENT [1-4]:"

# For your agent number, find test groups:
# Agent 1: Group 1-12 (see "Test Categories" section)
# Agent 2: Group 1-10
# Agent 3: Group 1-9
# Agent 4: Group 1-8
```

---

## ✍️ Step 3: Create Test File

### File Naming Convention
```
tests/test_agent{N}_{topic}.py
```

### Minimal Test Template
```python
"""Test suite for {module_name}."""
import pytest
from unittest.mock import MagicMock, patch
from python_backend.pythia_mining.{module} import {Class}

class Test{ClassName}:
    """Test {ClassName} functionality."""
    
    def setup_method(self):
        """Set up before each test."""
        self.instance = {Class}()
    
    def test_basic_initialization(self):
        """Test basic initialization."""
        assert self.instance is not None
    
    def test_feature_x(self):
        """Test feature X behavior."""
        result = self.instance.method_x()
        assert result is not None
```

---

## ⚡ Step 4: Run Your Tests

```bash
# Test single file
pytest tests/test_agent{N}_{topic}.py -v

# Test all your agent files
pytest tests/test_agent{N}_*.py -v

# With coverage
pytest tests/test_agent{N}_*.py -v --cov=python_backend/pythia_mining --cov-report=term-missing

# Show slowest tests
pytest tests/test_agent{N}_*.py -v --durations=10
```

---

## 🔍 Step 5: Coverage Goals

### Target Modules (Your Agent)

**Agent 1:**
```python
# Key files to cover (80%+)
python_backend/pythia_mining/phi_unified_mining_engine.py
python_backend/pythia_mining/mining_orchestrator.py
python_backend/pythia_mining/phi_config.py
```

**Agent 2:**
```python
python_backend/pythia_mining/live_stratum_session.py
python_backend/pythia_mining/pool_profiles.py
python_backend/pythia_mining/stratum_client.py
```

**Agent 3:**
```python
python_backend/pythia_mining/quantum_solver.py
python_backend/pythia_mining/quantum_regeneration.py
python_backend/pythia_mining/grover_quantum_solver.py
```

**Agent 4:**
```python
python_backend/pythia_mining/pulvini_phi_memory.py
python_backend/pythia_mining/pulvini_memory_compression_proof.py
python_backend/pythia_mining/mining_knowledge_base.py
```

---

## 🛠️ Essential Test Patterns

### Pattern 1: Basic Unit Test
```python
def test_method_returns_expected_value(self):
    """Test that method returns expected value."""
    obj = MyClass(config={"key": "value"})
    result = obj.method()
    assert result == expected_value
```

### Pattern 2: Error Handling
```python
def test_method_raises_on_invalid_input(self):
    """Test that method raises exception on invalid input."""
    with pytest.raises(ValueError):
        obj.method(invalid_arg=None)
```

### Pattern 3: Mock External Dependencies
```python
@patch('python_backend.pythia_mining.external_module.function')
def test_method_with_mocked_dependency(self, mock_func):
    """Test method with mocked external call."""
    mock_func.return_value = "mocked_result"
    obj = MyClass()
    result = obj.method()
    assert result == "expected"
    mock_func.assert_called_once()
```

### Pattern 4: Async Tests
```python
@pytest.mark.asyncio
async def test_async_method(self):
    """Test async method."""
    obj = MyClass()
    result = await obj.async_method()
    assert result is not None
```

### Pattern 5: Parameterized Tests
```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_method_multiple_inputs(self, input, expected):
    """Test method with multiple inputs."""
    obj = MyClass()
    assert obj.double(input) == expected
```

---

## 📊 Verification Checklist

Before submitting your tests:

- [ ] All test files created under `tests/test_agent{N}_*.py`
- [ ] At least 40+ tests written for your agent
- [ ] Run: `pytest tests/test_agent{N}_*.py -v` → all pass
- [ ] Check coverage: `pytest tests/test_agent{N}_*.py --cov --cov-report=term-missing`
- [ ] Coverage for target modules is **80%+**
- [ ] No test takes >2 seconds
- [ ] No flaky tests (run 2x to verify consistency)
- [ ] All tests have docstrings
- [ ] Mocks are used appropriately (not overmocked)
- [ ] Edge cases tested (empty, null, boundary values)
- [ ] Error paths tested (exceptions, timeouts, failures)

---

## 🚨 Common Pitfalls to Avoid

❌ **DON'T:**
- Create tests that depend on external services
- Write tests that take >2 seconds each
- Use hardcoded paths or assumptions
- Skip error handling tests
- Mock too heavily (test real behavior)
- Leave TODOs in test code

✅ **DO:**
- Isolate each test (use fixtures)
- Test one thing per test
- Use descriptive test names
- Cover error cases explicitly
- Mock external dependencies only
- Clean up resources (fixtures teardown)

---

## 📞 Support & Escalation

### Issue: Import Error
```bash
# Solution: Ensure Python path is correct
export PYTHONPATH=/Users/demouser/Desktop/HYBA_FULLSTACK:$PYTHONPATH
```

### Issue: Test Fails Intermittently
```bash
# Run test 5 times to check for flakiness
pytest tests/test_agent{N}_{test_name}.py -v --count=5
```

### Issue: Coverage Not Increasing
```bash
# Check what's being tested vs not
pytest tests/test_agent{N}_*.py --cov --cov-report=html
# Then open htmlcov/index.html and look for red lines
```

---

## 📈 Success Metrics

**Per Agent:**
- ✅ 40+ new tests written
- ✅ 80%+ coverage on target modules
- ✅ 100% test pass rate
- ✅ Average test duration <1 second
- ✅ Zero flaky tests

**Combined (All 4 Agents):**
- ✅ 160+ new tests total
- ✅ 80%+ overall coverage
- ✅ ~16 second total execution time
- ✅ Ready for production

---

## 🚀 Next Steps

1. **Read** detailed plan: `TEST_COVERAGE_PLAN_4_AGENTS.md`
2. **Create** first test file for your agent
3. **Run** tests locally: `pytest tests/test_agent{N}_*.py -v`
4. **Check** coverage: `pytest tests/test_agent{N}_*.py --cov`
5. **Iterate** until 80%+ coverage achieved
6. **Submit** for merge

---

## Example: Writing Your First Test File

```python
# tests/test_agent1_example.py
"""Test unified mining engine initialization."""
import pytest
from python_backend.pythia_mining.phi_unified_mining_engine import UnifiedMiningEngine

class TestUnifiedMiningEngineInitialization:
    """Test engine initialization scenarios."""
    
    def test_default_initialization(self):
        """Test engine initializes with default config."""
        engine = UnifiedMiningEngine()
        assert engine is not None
        assert engine.configured_capacity_ehs is not None
    
    def test_custom_capacity_initialization(self):
        """Test engine initializes with custom capacity."""
        engine = UnifiedMiningEngine(configured_capacity_ehs=100.0)
        assert engine.configured_capacity_ehs == 100.0
    
    @pytest.mark.parametrize("capacity", [0.1, 1.0, 10.0])
    def test_various_capacities(self, capacity):
        """Test engine initialization with various capacities."""
        engine = UnifiedMiningEngine(configured_capacity_ehs=capacity)
        assert engine.configured_capacity_ehs == capacity
    
    def test_invalid_capacity_raises_error(self):
        """Test that invalid capacity raises error."""
        with pytest.raises(Exception):
            UnifiedMiningEngine(configured_capacity_ehs=-1.0)

# Run with: pytest tests/test_agent1_example.py -v
```

---

**Deadline:** Target 80%+ coverage by end of this sprint
**Status:** Ready to execute
**Questions:** Contact QA Lead

Good luck! 🚀
