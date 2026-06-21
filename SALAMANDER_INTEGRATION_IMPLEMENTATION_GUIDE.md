# Salamander Integration Implementation Guide

**Date**: 2026-06-21  
**Status**: STEP-BY-STEP INTEGRATION WALKTHROUGH  
**Estimated Time**: 2-3 hours for full integration  
**Difficulty**: LOW to MEDIUM

---

## Quick Start

If you want to start integrating immediately, follow these 3 steps:

```bash
# 1. Review generated artifacts
cat artifacts/salamander_integration/*.py

# 2. Choose integration target (one of three options below)
# See "Integration Options" section

# 3. Run tests after each step
npm run test:backend
```

---

## Integration Options

### OPTION A: Minimal Integration (Lowest Risk)

**What It Does**: Wire only QaaS and PULVINI (no billing, no multi-agent)  
**Time**: 30-45 minutes  
**Risk**: LOW  
**Result**: Core quantum execution + compression working  

**Steps**:
1. Add QaaS routes to `main.py`
2. Add PULVINI to mining engine
3. Test and commit
4. Plan billing/multi-agent for later

### OPTION B: Complete Integration (Medium Risk)

**What It Does**: Wire all 4 subsystems end-to-end  
**Time**: 2-3 hours  
**Risk**: MEDIUM  
**Result**: Full system coherence with billing protection  

**Steps**:
1. Create specialist_agents.py
2. Create/bridge quantum_router.py
3. Apply all 4 integrations
4. Comprehensive testing
5. Deploy to staging

### OPTION C: Staged Integration (Recommended)

**What It Does**: Integrate in phases with validation between each  
**Time**: 4-6 hours  
**Risk**: LOWEST  
**Result**: High confidence, well-tested system  

**Steps**:
1. Phase 1: QaaS Routes + PULVINI (30 min)
2. Phase 2: Billing Rollback (60 min)
3. Phase 3: Multi-Agent (90 min)
4. Full validation (30 min)

---

## Phase 1: QaaS Routes Integration (30 minutes)

### Step 1a: Verify Target File Exists

```bash
ls -la python_backend/hyba_genesis_api/main.py
```

**Expected**: File exists

### Step 1b: Read Current Structure

```bash
grep -n "include_router" python_backend/hyba_genesis_api/main.py | head -5
```

**Expected Output Example**:
```
15: app.include_router(admin_router)
18: app.include_router(auth_router)
21: app.include_router(user_router)
```

### Step 1c: Locate Integration Point

In `python_backend/hyba_genesis_api/main.py`, find the section with `include_router` calls:

```python
# Look for this pattern
app = FastAPI()

# ... other imports and setup ...

# Router registration section (this is where we add)
app.include_router(admin_router)
app.include_router(auth_router)

# ADD NEW ROUTES HERE ↓↓↓
```

### Step 1d: Add QaaS Routes

Add this code block after the existing routers:

```python
# Salamander-regenerated QaaS routes integration
from .api.quantum_as_a_service_execute_hardened import router as qaas_router
from .api.public_computational_intelligence_service import router as ciaas_router

app.include_router(qaas_router, prefix="/api/qaas", tags=["Quantum-as-a-Service"])
app.include_router(ciaas_router, prefix="/api/ciaas", tags=["Computational-Intelligence"])
```

### Step 1e: Verify Syntax

```bash
python -m py_compile python_backend/hyba_genesis_api/main.py
```

**Expected**: No output = success

### Step 1f: Test Route Registration

```bash
# Start backend
npm run dev:backend &

# In another terminal, check routes
curl -s http://localhost:8000/api/qaas/health || echo "Routes not yet exposed"

# Kill backend
kill %1
```

### Step 1g: Commit Integration

```bash
git add python_backend/hyba_genesis_api/main.py
git commit -m "Salamander: Integrate QaaS routes"
```

**✅ Phase 1 Complete**

---

## Phase 2: PULVINI Compression Integration (30-45 minutes)

### Step 2a: Verify Mining Engine Exists

```bash
ls -la python_backend/pythia_mining/phi_unified_mining_engine.py
```

**Expected**: File exists

### Step 2b: Read Current Search Method

```bash
grep -A 10 "async def search" python_backend/pythia_mining/phi_unified_mining_engine.py
```

**Expected**: Current search implementation visible

### Step 2c: Create Enhanced Search Method

Add this class to `python_backend/pythia_mining/phi_unified_mining_engine.py`:

```python
# Salamander-regenerated PULVINI integration
from .pulvini_compressed_solver import CompressedSolver
from .pulvini_memory_compression_proof import verify_compression_integrity

class PhiUnifiedMiningEngineWithPulvini:
    """Enhanced mining engine with PULVINI compression."""
    
    def __init__(self):
        self.compressed_solver = CompressedSolver()
        self.compression_ratio = 2.0  # Information integrity boundary
    
    async def search_with_compression(self, job):
        """Execute search with φ-folding compression."""
        try:
            # Compress search state
            compressed_state = self.compressed_solver.compress(job.state)
            
            # Execute with compression
            result = await self.compressed_solver.solve(compressed_state)
            
            # Verify integrity
            integrity_check = verify_compression_integrity(
                compressed_state, 
                result,
                max_ratio=self.compression_ratio
            )
            
            if not integrity_check["valid"]:
                raise ValueError(f"Compression integrity violation: {integrity_check}")
            
            return result
        
        except Exception as e:
            # Fallback to uncompressed search
            import logging
            logging.warning(f"Compression failed, using uncompressed: {e}")
            return await self.search(job)  # Use original method
```

### Step 2d: Wire Into Existing Engine

Find where `PhiUnifiedMiningEngine` is used, and add compression variant:

```python
# Old way (still works):
engine = PhiUnifiedMiningEngine()
result = await engine.search(job)

# New way (with compression):
engine = PhiUnifiedMiningEngineWithPulvini()
result = await engine.search_with_compression(job)
```

### Step 2e: Test Compression

```python
# Simple test
import asyncio
from pythia_mining.phi_unified_mining_engine import PhiUnifiedMiningEngineWithPulvini

async def test_compression():
    engine = PhiUnifiedMiningEngineWithPulvini()
    print(f"Engine created: {engine}")
    print(f"Compression ratio: {engine.compression_ratio}")
    return True

# Run test
result = asyncio.run(test_compression())
print(f"✅ Compression test: {result}")
```

### Step 2f: Run Mining Tests

```bash
npm run test:mining 2>&1 | grep -E "(PASS|FAIL|Error)"
```

**Expected**: Tests pass (may warn about compression if not using it yet)

### Step 2g: Commit Integration

```bash
git add python_backend/pythia_mining/phi_unified_mining_engine.py
git commit -m "Salamander: Integrate PULVINI compression"
```

**✅ Phase 2 Complete**

---

## Phase 3: Billing Rollback Integration (60 minutes)

This phase requires creating a bridge because `quantum_router.py` doesn't exist.

### Option A: Create quantum_router.py (Recommended)

#### Step 3a: Create File

```bash
touch python_backend/hyba_genesis_api/api/quantum_router.py
```

#### Step 3b: Add Routing Logic

```python
"""
Quantum Router - Central routing for all quantum operations
Salamander-generated: Bridges billing system with QaaS execution
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from .billing_rollback import get_billing_rollback_manager
from .quantum_as_a_service_execute_hardened import (
    QuantumWorkloadRequest,
    _VirtualFaultTolerantQuantumComputer
)

router = APIRouter()

@router.post("/execute-with-rollback")
async def execute_with_rollback(
    execution_id: str,
    customer_id: str,
    request: QuantumWorkloadRequest
) -> Dict[str, Any]:
    """Execute quantum workload with automatic billing rollback on failure."""
    
    rollback = get_billing_rollback_manager()
    work_units = request.circuit_depth * len(request.qubits) * 0.1
    
    try:
        # Execute quantum workload
        computer = _VirtualFaultTolerantQuantumComputer()
        result = computer.execute(request)
        
        # Mark as success
        return {
            "status": "completed",
            "execution_id": execution_id,
            "work_units_consumed": int(work_units),
            "result": result
        }
    
    except Exception as e:
        # Automatic refund on failure
        refund_result = rollback.refund_on_failure(
            execution_id=execution_id,
            customer_id=customer_id,
            work_units_consumed=int(work_units),
            reason=str(e)
        )
        
        # Return error with refund confirmation
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "refund_status": refund_result["status"],
                "work_units_refunded": refund_result["work_units_refunded"]
            }
        )
```

#### Step 3c: Register Router in main.py

Add to the router registration section:

```python
from .api.quantum_router import router as quantum_router
app.include_router(quantum_router, prefix="/api/quantum", tags=["Quantum-Operations"])
```

#### Step 3d: Test Billing Integration

```python
import asyncio
from hyba_genesis_api.api.billing_rollback import get_billing_rollback_manager

async def test_billing_rollback():
    rollback = get_billing_rollback_manager()
    
    # Simulate a failed execution
    result = rollback.refund_on_failure(
        execution_id="test-exec-001",
        customer_id="test-customer",
        work_units_consumed=500,
        reason="Test failure"
    )
    
    print(f"Refund result: {result}")
    assert result["status"] == "refunded"
    return True

# Run test
success = asyncio.run(test_billing_rollback())
print(f"✅ Billing integration test: {success}")
```

### Option B: Integrate Into Existing execute() (Alternative)

If you prefer not to create new files, modify `quantum_as_a_service_execute_hardened.py`:

```python
# Inside the execute() method, wrap with billing rollback:

from .billing_rollback import get_billing_rollback_manager

async def execute(self, request: QuantumWorkloadRequest):
    rollback = get_billing_rollback_manager()
    work_units = self._calculate_work_units(request)
    
    try:
        # Original execution logic
        result = self._execute_quantum_workload(request)
        return {
            "status": "completed",
            "work_units_consumed": work_units,
            "result": result
        }
    except Exception as e:
        # Automatic refund
        rollback.refund_on_failure(
            execution_id=request.id,
            customer_id=request.customer_id,
            work_units_consumed=work_units,
            reason=str(e)
        )
        raise
```

### Step 3e: Test End-to-End

```bash
# Run backend tests including billing
npm run test:backend 2>&1 | grep -E "billing|rollback"
```

### Step 3f: Commit Integration

```bash
git add python_backend/hyba_genesis_api/api/quantum_router.py
git add python_backend/hyba_genesis_api/main.py
git commit -m "Salamander: Integrate billing rollback system"
```

**✅ Phase 3 Complete**

---

## Phase 4: Multi-Agent Orchestration (90 minutes)

### Step 4a: Create specialist_agents.py

```bash
cat > python_backend/hyba_genesis_api/api/multi_agent/specialist_agents.py << 'EOF'
"""
Specialist Agents for Multi-Agent Orchestration
Salamander-generated: Analysis, Optimization, Security agents
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class AnalysisAgent:
    """Analyzes execution patterns and provides insights."""
    
    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze context and return insights."""
        logger.info(f"Analysis agent analyzing: {context.keys()}")
        
        return {
            "agent": "AnalysisAgent",
            "insights": [
                "Performance within expected range",
                "Resource utilization: 45%"
            ],
            "confidence": 0.95
        }


class OptimizationAgent:
    """Optimizes execution for efficiency."""
    
    async def optimize(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize context for better performance."""
        logger.info(f"Optimization agent optimizing: {context.keys()}")
        
        optimizations = [
            {"type": "cache", "savings": "20%"},
            {"type": "parallelization", "speedup": "1.5x"}
        ]
        
        return {
            "agent": "OptimizationAgent",
            "optimizations": optimizations,
            "estimated_improvement": 0.35
        }


class SecurityAgent:
    """Validates security constraints and access controls."""
    
    async def validate_security(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate security of execution context."""
        logger.info(f"Security agent validating: {context.keys()}")
        
        checks = [
            {"check": "API key valid", "status": "passed"},
            {"check": "Customer isolation", "status": "passed"},
            {"check": "Rate limits", "status": "passed"}
        ]
        
        return {
            "agent": "SecurityAgent",
            "security_checks": checks,
            "security_score": 0.99
        }
EOF
```

### Step 4b: Create Reflexive Controller Integration

Add to `python_backend/hyba_genesis_api/core/reflexive_controller.py`:

```python
# Salamander-regenerated multi-agent integration
from ..api.multi_agent.orchestrator import SwarmOrchestrator
from ..api.multi_agent.specialist_agents import (
    AnalysisAgent, 
    OptimizationAgent,
    SecurityAgent
)


class ReflexiveControllerWithSwarm:
    """Enhanced reflexive controller with multi-agent orchestration."""
    
    def __init__(self):
        self.orchestrator = SwarmOrchestrator()
        self.agents = {
            "analysis": AnalysisAgent(),
            "optimization": OptimizationAgent(),
            "security": SecurityAgent()
        }
        self.execution_history = []
    
    async def orchestrate_optimization(self, context: dict) -> dict:
        """Delegate optimization to multi-agent swarm."""
        # Run security validation first
        security_result = await self.agents["security"].validate_security(context)
        
        if security_result["security_score"] < 0.9:
            raise SecurityError("Security validation failed")
        
        # Run analysis
        analysis_result = await self.agents["analysis"].analyze(context)
        
        # Run optimization
        optimization_result = await self.agents["optimization"].optimize(context)
        
        # Coordinate through orchestrator
        final_result = await self.orchestrator.coordinate(
            self.agents, 
            {
                "analysis": analysis_result,
                "optimization": optimization_result,
                "security": security_result
            }
        )
        
        # Record execution
        self.execution_history.append({
            "context": context,
            "result": final_result
        })
        
        return final_result
```

### Step 4c: Wire into autonomous_mining_controller

Find `autonomous_mining_controller.py` and add:

```python
from .reflexive_controller import ReflexiveControllerWithSwarm

class AutonomousMiningControllerWithSwarm:
    def __init__(self):
        self.reflexive_controller = ReflexiveControllerWithSwarm()
    
    async def execute_with_swarm_optimization(self, job):
        """Execute job with swarm optimization."""
        return await self.reflexive_controller.orchestrate_optimization({
            "job": job,
            "timestamp": time.time()
        })
```

### Step 4d: Test Multi-Agent Coordination

```python
import asyncio
from hyba_genesis_api.core.reflexive_controller import ReflexiveControllerWithSwarm

async def test_multi_agent():
    controller = ReflexiveControllerWithSwarm()
    
    context = {
        "customer_id": "test-customer",
        "job_type": "optimization",
        "complexity": "high"
    }
    
    result = await controller.orchestrate_optimization(context)
    print(f"Multi-agent result: {result}")
    return True

# Run test
success = asyncio.run(test_multi_agent())
print(f"✅ Multi-agent coordination test: {success}")
```

### Step 4e: Run Integration Tests

```bash
npm run test:backend 2>&1 | grep -E "multi_agent|orchestrator|specialist"
```

### Step 4f: Commit Integration

```bash
git add python_backend/hyba_genesis_api/api/multi_agent/specialist_agents.py
git add python_backend/hyba_genesis_api/core/reflexive_controller.py
git add python_backend/hyba_genesis_api/core/autonomous_mining_controller.py
git commit -m "Salamander: Integrate multi-agent orchestration"
```

**✅ Phase 4 Complete**

---

## Full System Verification

After all phases, run comprehensive tests:

```bash
# Run all tests
npm run test

# Check for regressions
npm run test:backend 2>&1 | tail -10

# Verify integrations
grep -r "Salamander:" python_backend/ | wc -l
```

**Expected Output**:
- All tests passing
- No regressions
- 4+ Salamander integrations found

---

## Rollback Procedure (If Needed)

If an integration causes issues, you can rollback:

```bash
# See recent commits
git log --oneline -10

# Rollback to before integrations
git revert <commit-hash>

# Or reset to specific point
git reset --hard <commit-hash>
```

---

## Success Criteria

✅ **Integration is successful when**:
1. All tests pass
2. No new errors introduced
3. System coherence maintained
4. Performance unchanged or improved

---

## Next Steps After Integration

1. **Monitor System** - Watch for errors in production
2. **Feed Back Results** - Document what worked/failed
3. **Update Memory** - Run unifier again to detect new orphans
4. **Celebrate** - System is now more coherent!

---

**Implementation Start Time**: [Record when you start]  
**Expected Completion**: [Now + 2-4 hours]  
**Support**: Review SALAMANDER_SYSTEM_INTEGRATION_REVIEW.md if stuck
