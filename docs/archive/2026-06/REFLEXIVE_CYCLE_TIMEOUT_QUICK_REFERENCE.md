# Reflexive Cycle Timeout Guard - Quick Reference

## 30-Second Overview

The `ReflexiveCycleGuard` enforces a **100ms hard deadline** on reflexive mining cycles with graceful degradation:

- **Cancels** AST parsing operations
- **Interrupts** virtual mining simulations  
- **Validates** constraints (skips if timeout)
- **Applies** proposals with automatic rollback on timeout
- **Never** leaves system in inconsistent state
- **Returns** best available results when timeout occurs

## Installation

```python
# File: python_backend/pythia_mining/reflexive_cycle_timeout.py
from python_backend.pythia_mining.reflexive_cycle_timeout import ReflexiveCycleGuard
```

## Minimal Example

```python
from python_backend.pythia_mining.reflexive_cycle_timeout import ReflexiveCycleGuard

guard = ReflexiveCycleGuard(deadline_ms=100.0)

async def my_cycle():
    async with guard.reflexive_cycle() as cycle:
        # Phase 1: Parse proposals
        proposals = await cycle.parse_proposals(parse_fn)
        
        # Phase 2: Simulate mining
        simulated = await cycle.simulate_mining(proposals, sim_fn)
        
        # Phase 3: Validate constraints
        validated = await cycle.validate_constraints(simulated, val_fn)
        
        # Phase 4: Apply proposals
        applied, was_complete = await cycle.apply_proposals(validated, apply_fn)
        
        return applied
```

## API Cheat Sheet

| Operation | Usage | Timeout Behavior |
|-----------|-------|------------------|
| **Parse** | `proposals = await cycle.parse_proposals(parse_fn)` | Returns `[]` |
| **Simulate** | `simulated = await cycle.simulate_mining(proposals, sim_fn)` | Returns partial results |
| **Validate** | `validated = await cycle.validate_constraints(proposals, val_fn)` | Skips remaining checks (default) |
| **Apply** | `applied, complete = await cycle.apply_proposals(proposals, apply_fn)` | Rolls back, returns partial + `complete=False` |

## Check Timeout

```python
async with guard.reflexive_cycle() as cycle:
    remaining_ms = cycle.time_remaining_ms()
    is_exceeded = cycle.is_deadline_exceeded()
    
    if remaining_ms < 20:
        # Less than 20ms left
        pass
```

## Monitor Health

```python
from python_backend.pythia_mining.reflexive_cycle_integration import ReflexiveCycleMonitor

monitor = ReflexiveCycleMonitor(guard)
report = monitor.get_health_report()

print(f"Status: {report['health_status']}")  # HEALTHY, WARNING, CRITICAL
print(f"Timeout rate: {report['timeout_rate_percent']}%")
print(f"Safety margin: {report['safety_margin_ms']}ms")

monitor.log_health_report()  # Log to logger
```

## Get Metrics

```python
metrics = guard.get_metrics_snapshot()

# Returns:
{
    "timeout_count": 2,
    "total_cycles": 50,
    "avg_duration_ms": 45.2,
    "min_duration_ms": 20.1,
    "max_duration_ms": 99.8,
    "partial_results_returned": 3,
    "validations_skipped": 5,
    "rollbacks_performed": 2,
    "last_timeout_reason": "...",
}
```

## Integration with AutonomousMiningController

```python
from python_backend.pythia_mining.reflexive_cycle_integration import ReflexiveCycleIntegration

class AutonomousMiningController:
    def __init__(self):
        self.reflexive_guard = ReflexiveCycleGuard()
        self.integration = ReflexiveCycleIntegration(self, self.reflexive_guard)
    
    async def _run_reflexive_cycle(self):
        return await self.integration.run_protected_reflexive_cycle()
```

## Use Global Guard

```python
from python_backend.pythia_mining.reflexive_cycle_timeout import (
    get_reflexive_cycle_guard,
    reset_reflexive_cycle_guard,
)

guard = get_reflexive_cycle_guard()  # Get or create global

reset_reflexive_cycle_guard()  # Reset for testing
```

## Execution Phases

| Phase | Purpose | Timeout Behavior |
|-------|---------|------------------|
| **PARSING** | Generate proposals from AST | Returns `[]` |
| **SIMULATION** | Virtual mining simulations | Returns best proposals found |
| **VALIDATION** | Constraint checking | Skips remaining checks |
| **APPLYING** | Apply to live system | Rolls back, maintains consistency |

## Timeout Strategies

### Graceful Degradation (Default)
```python
# Returns partial results, continues cycle
validated = await cycle.validate_constraints(
    simulated,
    val_fn,
    skip_on_timeout=True  # Default: skip validation on timeout
)
```

### All-or-Nothing (Strict)
```python
# Raises on timeout instead of skipping
try:
    validated = await cycle.validate_constraints(
        simulated,
        val_fn,
        skip_on_timeout=False  # Raise on timeout
    )
except asyncio.TimeoutError:
    logger.error("Validation incomplete")
```

### Safe Rollback (Default)
```python
# Automatically rollback if apply times out
applied, was_complete = await cycle.apply_proposals(
    validated,
    apply_fn,
    rollback_on_timeout=True  # Default: rollback on timeout
)

if not was_complete:
    logger.warning("Rolled back due to timeout")
```

## Common Patterns

### Pattern 1: Check Before Starting Long Operation
```python
async with guard.reflexive_cycle() as cycle:
    if cycle.time_remaining_ms() < 50:
        logger.warning("Not enough time for full cycle")
        return []
```

### Pattern 2: Handle Partial Results
```python
async with guard.reflexive_cycle() as cycle:
    proposals = await cycle.parse_proposals(parse_fn)
    simulated = await cycle.simulate_mining(proposals, sim_fn)
    
    # May be partial if timeout
    logger.info(f"Simulated {len(simulated)}/{len(proposals)} proposals")
```

### Pattern 3: Monitor Cycle Completion
```python
async with guard.reflexive_cycle() as cycle:
    applied, was_complete = await cycle.apply_proposals(proposals, apply_fn)
    
    if not was_complete:
        logger.warning(f"Incomplete: {len(applied)}/{len(proposals)} applied")
        # System is still consistent due to rollback
```

### Pattern 4: Continuous Monitoring
```python
monitor = ReflexiveCycleMonitor(guard)

# Run cycles...

# Check health periodically
if monitor.get_health_report()["health_status"] != "HEALTHY":
    logger.error("Reflexive cycles unhealthy")
    # Increase deadline or reduce workload
```

## Troubleshooting

| Problem | Symptom | Solution |
|---------|---------|----------|
| **Too many timeouts** | `timeout_count` high | Increase deadline: `ReflexiveCycleGuard(deadline_ms=150)` |
| **Inconsistent state** | System breaks after timeout | Ensure `rollback_on_timeout=True` |
| **Partial results not OK** | Need all-or-nothing | Use `skip_on_timeout=False` |
| **Missing rollbacks** | State inconsistency | Check `rollback_count` in metrics |

## Performance Tuning

```python
# Monitor current performance
monitor = ReflexiveCycleMonitor(guard)
report = monitor.get_health_report()

if report["timeout_rate_percent"] > 10:
    # Increase deadline
    guard.deadline_ms = 150.0
elif report["safety_margin_ms"] < 10:
    # Optimize proposal generation
    proposals = await cycle.parse_proposals(parse_fn, limit_count=5)
```

## Files

| File | Purpose |
|------|---------|
| `reflexive_cycle_timeout.py` | Main guard implementation |
| `reflexive_cycle_integration.py` | Integration with controller |
| `docs/REFLEXIVE_CYCLE_TIMEOUT_GUIDE.md` | Full documentation |
| `tests/test_reflexive_cycle_timeout.py` | Comprehensive tests |

## Key Features

✅ **100ms Hard Deadline** - Prevents cascade failures  
✅ **Graceful Degradation** - Returns best available results  
✅ **State Safety** - Never inconsistent, rollback on timeout  
✅ **Partial Results** - Continue with what's available  
✅ **Comprehensive Telemetry** - Full metrics on all timeouts  
✅ **No Hanged Coroutines** - Proper task cancellation  
✅ **Exception Safe** - Proper error handling and recovery  
✅ **Easy Integration** - Works with existing controller  

## Example: Full Integration

```python
from python_backend.pythia_mining.reflexive_cycle_timeout import ReflexiveCycleGuard
from python_backend.pythia_mining.reflexive_cycle_integration import (
    ReflexiveCycleIntegration,
    ReflexiveCycleMonitor,
)

class MyAutonomousController:
    def __init__(self):
        self.guard = ReflexiveCycleGuard(deadline_ms=100.0)
        self.integration = ReflexiveCycleIntegration(self, self.guard)
        self.monitor = ReflexiveCycleMonitor(self.guard)
    
    async def run_mining_cycle(self):
        try:
            # Run protected cycle
            proposals = await self.integration.run_protected_reflexive_cycle()
            
            # Check health
            if self.monitor.get_health_report()["health_status"] != "HEALTHY":
                self.logger.warning("Reflexive cycles degraded")
            
            return proposals
        
        except Exception as e:
            self.logger.error(f"Cycle failed: {e}")
            raise
```

## See Also

- Full documentation: `docs/REFLEXIVE_CYCLE_TIMEOUT_GUIDE.md`
- Integration examples: `reflexive_cycle_integration.py`
- Test suite: `tests/test_reflexive_cycle_timeout.py`
- Source: `reflexive_cycle_timeout.py`
