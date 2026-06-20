# Reflexive Cycle Timeout Guard Documentation

## Overview

The `ReflexiveCycleGuard` class enforces a hard 100ms deadline on reflexive mining cycles, preventing cascade failures from long-running counterfactual operations. It provides:

- **Graceful timeout handling** with partial result returns
- **Four-phase execution tracking**: Parsing → Simulation → Validation → Applying
- **Automatic rollback** on timeout to maintain system consistency
- **Comprehensive telemetry** on cycle execution and performance
- **No hanged coroutines** with proper task cancellation and exception handling
- **Safe state recovery** with validated rollback mechanisms

## Architecture

### Core Components

```
ReflexiveCycleGuard (main class)
├── ExecutionPhase (enum) - Tracks which phase is active
├── PhaseMetrics (dataclass) - Per-phase timing and metrics
├── TimeoutMetrics (dataclass) - Aggregated metrics
├── CycleContext (context manager helper)
└── TimeoutAction (enum) - Actions taken on timeout
```

### Key Design Principles

1. **100ms Hard Deadline**: Prevents any reflexive cycle from hanging beyond 100ms
2. **Graceful Degradation**: Returns best available results rather than failing
3. **State Safety**: Never leaves system in inconsistent state through rollbacks
4. **Partial Results**: When timeout occurs, returns what was completed
5. **Comprehensive Logging**: Every timeout and recovery is logged with context

## Usage

### Basic Usage

```python
from python_backend.pythia_mining.reflexive_cycle_timeout import ReflexiveCycleGuard

# Create a guard instance
guard = ReflexiveCycleGuard(deadline_ms=100.0, enable_telemetry=True)

# Use in an async context
async def my_reflexive_cycle():
    async with guard.reflexive_cycle() as cycle:
        # Phase 1: Parse proposals
        proposals = await cycle.parse_proposals(
            parse_fn,
            targets=["target1", "target2"]
        )
        
        # Phase 2: Simulate mining
        simulated = await cycle.simulate_mining(proposals, simulation_fn)
        
        # Phase 3: Validate constraints
        validated = await cycle.validate_constraints(
            simulated,
            validation_fn,
            skip_on_timeout=True  # Continue cycle if validation times out
        )
        
        # Phase 4: Apply proposals
        applied, was_complete = await cycle.apply_proposals(
            validated,
            apply_fn,
            rollback_on_timeout=True  # Rollback if apply times out
        )
        
        return applied
```

### Integration with AutonomousMiningController

```python
from python_backend.pythia_mining.reflexive_cycle_integration import (
    ReflexiveCycleIntegration,
    ReflexiveCycleMonitor,
)

class AutonomousMiningController:
    def __init__(self, ...):
        self.reflexive_guard = ReflexiveCycleGuard(deadline_ms=100.0)
        self.reflexive_integration = ReflexiveCycleIntegration(
            self,
            self.reflexive_guard
        )
        self.reflexive_monitor = ReflexiveCycleMonitor(self.reflexive_guard)
    
    async def _run_reflexive_cycle(self):
        """Run reflexive cycle with timeout protection."""
        return await self.reflexive_integration.run_protected_reflexive_cycle()
    
    async def seek_improvement(self):
        """Seek improvements with comprehensive monitoring."""
        proposals = await self._run_reflexive_cycle()
        
        # Log health report
        self.reflexive_monitor.log_health_report()
        
        return proposals
```

### Using Global Guard

```python
from python_backend.pythia_mining.reflexive_cycle_timeout import (
    get_reflexive_cycle_guard,
    reset_reflexive_cycle_guard,
)

# Get or create global guard
guard = get_reflexive_cycle_guard(deadline_ms=100.0)

# Reset for testing
reset_reflexive_cycle_guard()
```

## Execution Phases

### Phase 1: Parsing (ExecutionPhase.PARSING)

**Purpose**: Generate optimization proposals from code analysis

**Timeout Behavior**: 
- Returns empty proposal list if parsing exceeds time budget
- Allows cycle to continue with graceful degradation

**Example**:
```python
proposals = await cycle.parse_proposals(
    async def parse():
        # Analyze AST, identify optimization targets
        # Generate proposals
        return [proposal1, proposal2, ...]
)

if not proposals:
    logger.warning("No proposals generated before timeout")
```

### Phase 2: Simulation (ExecutionPhase.SIMULATION)

**Purpose**: Simulate virtual mining with each proposal

**Timeout Behavior**:
- Returns proposals completed so far
- Skips remaining proposals gracefully
- Allows best proposals found to be validated and applied

**Example**:
```python
simulated = await cycle.simulate_mining(
    proposals,
    async def simulate(proposal):
        # Run virtual mining simulation
        # Calculate expected phi improvement
        return {**proposal, "simulated_phi": 0.95}
)

# May have partial results if timeout
assert len(simulated) <= len(proposals)
```

### Phase 3: Validation (ExecutionPhase.VALIDATION)

**Purpose**: Check constraints against system limits

**Timeout Behavior**:
- By default: Skips remaining constraint checks (logs warning)
- Returns all proposals anyway to avoid losing work
- Optional: Raise error on timeout (strict mode)

**Example**:
```python
validated = await cycle.validate_constraints(
    simulated,
    async def validate(proposal):
        # Check safety constraints
        # Check resource boundaries
        return {**proposal, "valid": True}
    skip_on_timeout=True  # Skip validation on timeout
)

# All proposals returned, even if validation was skipped
```

### Phase 4: Applying (ExecutionPhase.APPLYING)

**Purpose**: Apply validated proposals to live system

**Timeout Behavior**:
- Automatically rollback pending applications on timeout
- Returns (partial_applied, was_complete) tuple
- Never leaves system in inconsistent state

**Example**:
```python
applied, was_complete = await cycle.apply_proposals(
    validated,
    async def apply(proposal):
        # Apply proposal to live system
        # Update configuration, restart services, etc.
        return {**proposal, "applied": True}
    rollback_on_timeout=True  # Rollback on timeout
)

if not was_complete:
    logger.warning(f"Incomplete: {len(applied)}/{len(validated)} applied")
```

## Timeout Handling Strategies

### Strategy 1: Graceful Degradation (Default)

Maximizes utility by returning best available results:

```python
async with guard.reflexive_cycle() as cycle:
    # Parse proposals
    proposals = await cycle.parse_proposals(parse_fn)
    if not proposals:
        return []  # No proposals generated
    
    # Simulate what we can
    simulated = await cycle.simulate_mining(proposals, sim_fn)
    
    # Skip validation if needed
    validated = await cycle.validate_constraints(
        simulated,
        val_fn,
        skip_on_timeout=True
    )
    
    # Apply what we can
    applied, complete = await cycle.apply_proposals(
        validated,
        apply_fn,
        rollback_on_timeout=True
    )
    
    return applied  # Return what was applied
```

### Strategy 2: All-or-Nothing (Strict Mode)

Fails cycle if constraints cannot be fully validated:

```python
async with guard.reflexive_cycle() as cycle:
    proposals = await cycle.parse_proposals(parse_fn)
    simulated = await cycle.simulate_mining(proposals, sim_fn)
    
    # Raise on validation timeout instead of skipping
    validated = await cycle.validate_constraints(
        simulated,
        val_fn,
        skip_on_timeout=False  # Raise on timeout
    )
    
    applied, _ = await cycle.apply_proposals(validated, apply_fn)
    return applied
```

### Strategy 3: Safe Rollback (Default)

Ensures consistency by rolling back partial applications:

```python
async with guard.reflexive_cycle() as cycle:
    proposals = await cycle.parse_proposals(parse_fn)
    simulated = await cycle.simulate_mining(proposals, sim_fn)
    validated = await cycle.validate_constraints(simulated, val_fn)
    
    # Rollback on timeout to maintain consistency
    applied, was_complete = await cycle.apply_proposals(
        validated,
        apply_fn,
        rollback_on_timeout=True  # Automatic rollback
    )
    
    if not was_complete:
        logger.warning("Rollback executed to maintain consistency")
```

## Metrics and Monitoring

### Available Metrics

```python
metrics = guard.get_metrics_snapshot()

# Returns:
{
    "timeout_count": 2,                    # Number of timeouts
    "total_cycles": 50,                    # Total cycles executed
    "avg_duration_ms": 45.2,               # Average cycle duration
    "min_duration_ms": 20.1,               # Minimum cycle duration
    "max_duration_ms": 99.8,               # Maximum cycle duration
    "percent_completed": 89.3,             # Average percent completed
    "phases_affected": ["simulation"],     # Which phases timed out
    "partial_results_returned": 3,         # Partial results count
    "validations_skipped": 5,              # Validations skipped
    "rollbacks_performed": 2,              # Rollbacks executed
    "recoveries_attempted": 1,             # Recovery attempts
    "last_timeout_reason": "...",          # Last timeout reason
    "last_timeout_timestamp": "2024-01-15T10:30:45.123Z"
}
```

### Health Monitoring

```python
from python_backend.pythia_mining.reflexive_cycle_integration import ReflexiveCycleMonitor

monitor = ReflexiveCycleMonitor(guard)

# Get health report
report = monitor.get_health_report()

# Log health report
monitor.log_health_report()

# Check health status
if report["health_status"] == "CRITICAL":
    logger.error("Reflexive cycles are timing out too frequently!")
elif report["health_status"] == "WARNING":
    logger.warning("Reflexive cycles have insufficient safety margin")
```

### Health Status Levels

- **HEALTHY**: <5% timeout rate, >10% safety margin
- **WARNING**: 5-10% timeout rate or <10% safety margin
- **CRITICAL**: >10% timeout rate

## Error Handling and Recovery

### Handling Timeouts

```python
async with guard.reflexive_cycle() as cycle:
    try:
        proposals = await cycle.parse_proposals(parse_fn)
        simulated = await cycle.simulate_mining(proposals, sim_fn)
        validated = await cycle.validate_constraints(simulated, val_fn)
        applied, was_complete = await cycle.apply_proposals(validated, apply_fn)
        
        if not was_complete:
            # Cycle completed but with timeout
            logger.warning("Cycle partially completed due to timeout")
        
        return applied
    
    except asyncio.TimeoutError:
        # Handle timeout explicitly if needed
        logger.error("Reflexive cycle exceeded timeout")
        raise
```

### Handling Phase Errors

```python
async with guard.reflexive_cycle() as cycle:
    try:
        proposals = await cycle.parse_proposals(parse_fn)
    except ValueError as e:
        logger.error(f"Parsing error: {e}")
        return []  # Graceful degradation
    
    try:
        simulated = await cycle.simulate_mining(proposals, sim_fn)
    except RuntimeError as e:
        logger.error(f"Simulation error: {e}")
        # Continue with original proposals
        simulated = proposals
```

### Automatic Rollback

```python
async with guard.reflexive_cycle() as cycle:
    validated = await cycle.validate_constraints(simulated, val_fn)
    
    # Rollback is automatic on timeout
    applied, was_complete = await cycle.apply_proposals(
        validated,
        apply_fn,
        rollback_on_timeout=True  # Automatic rollback
    )
    
    # System is always in consistent state after this call
    assert was_complete or len(applied) > 0  # Either complete or rolled back
```

## Performance Tuning

### Adjusting Deadline

```python
# Longer deadline for complex scenarios
guard = ReflexiveCycleGuard(deadline_ms=200.0)

# Shorter deadline for latency-sensitive operations
guard = ReflexiveCycleGuard(deadline_ms=50.0)
```

### Monitoring and Optimization

```python
# Run cycles and monitor
monitor = ReflexiveCycleMonitor(guard)

# If timeout rate is high:
if monitor.get_health_report()["timeout_rate_percent"] > 10:
    # Option 1: Increase deadline
    guard.deadline_ms = 150.0
    
    # Option 2: Reduce proposal count
    proposals = await cycle.parse_proposals(parse_fn, limit_count=5)
    
    # Option 3: Parallelize where possible
    simulated = await asyncio.gather(*[
        cycle.simulate_mining([p], sim_fn) 
        for p in proposals
    ])
```

## Testing

### Unit Tests

```python
import pytest
from python_backend.pythia_mining.reflexive_cycle_timeout import ReflexiveCycleGuard

@pytest.mark.asyncio
async def test_parsing_timeout():
    guard = ReflexiveCycleGuard(deadline_ms=50.0)
    
    async def slow_parse():
        await asyncio.sleep(0.1)  # Exceed deadline
        return []
    
    async with guard.reflexive_cycle() as cycle:
        proposals = await cycle.parse_proposals(slow_parse)
        assert proposals == []  # Graceful timeout handling
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_full_cycle_with_timeouts():
    guard = ReflexiveCycleGuard(deadline_ms=50.0)
    
    async with guard.reflexive_cycle() as cycle:
        proposals = await cycle.parse_proposals(parse_fn)
        simulated = await cycle.simulate_mining(proposals, sim_fn)
        validated = await cycle.validate_constraints(simulated, val_fn)
        applied, complete = await cycle.apply_proposals(validated, apply_fn)
        
        # Verify consistency
        assert len(applied) <= len(validated)
```

## Troubleshooting

### Problem: Frequent Timeouts

**Symptoms**: `timeout_count` increases rapidly

**Solutions**:
1. Increase deadline: `ReflexiveCycleGuard(deadline_ms=150.0)`
2. Reduce proposal count in parse phase
3. Optimize simulation function performance
4. Skip validation on timeout: `skip_on_timeout=True`

### Problem: Partial Results Not Acceptable

**Symptoms**: Application requires all-or-nothing semantics

**Solution**: 
```python
# Use strict mode
try:
    validated = await cycle.validate_constraints(
        simulated,
        val_fn,
        skip_on_timeout=False  # Raise on timeout
    )
except asyncio.TimeoutError:
    # Handle as complete failure
    logger.error("Validation incomplete, discarding cycle")
    return []
```

### Problem: Rollbacks Not Executing

**Symptoms**: System inconsistency after timeout

**Debug**:
```python
# Check rollback metrics
metrics = guard.get_metrics_snapshot()
print(f"Rollbacks performed: {metrics['rollbacks_performed']}")

# Ensure rollback_on_timeout=True
applied, complete = await cycle.apply_proposals(
    validated,
    apply_fn,
    rollback_on_timeout=True  # Ensure this is True
)
```

## Best Practices

1. **Always use context manager**: Ensures proper cleanup and metrics recording
2. **Handle partial results**: Check `was_complete` return value
3. **Enable telemetry**: Track performance with `enable_telemetry=True`
4. **Monitor health**: Use `ReflexiveCycleMonitor` regularly
5. **Log timeouts**: Always log timeout events for debugging
6. **Test graceful degradation**: Verify cycle works with partial results
7. **Implement rollback functions**: If custom state needs rollback
8. **Set reasonable timeout**: 100ms default, adjust based on workload

## API Reference

### ReflexiveCycleGuard

```python
class ReflexiveCycleGuard:
    def __init__(
        self,
        deadline_ms: float = 100.0,
        enable_telemetry: bool = True,
        logger: Optional[logging.Logger] = None,
    )
    
    @asynccontextmanager
    async def reflexive_cycle(self)
    
    async def parse_proposals(
        self,
        parse_fn: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Optional[List[Dict[str, Any]]]
    
    async def simulate_mining(
        self,
        proposals: List[Dict[str, Any]],
        simulation_fn: Any,
    ) -> List[Dict[str, Any]]
    
    async def validate_constraints(
        self,
        proposals: List[Dict[str, Any]],
        validation_fn: Any,
        skip_on_timeout: bool = True,
    ) -> List[Dict[str, Any]]
    
    async def apply_proposals(
        self,
        proposals: List[Dict[str, Any]],
        apply_fn: Any,
        rollback_on_timeout: bool = True,
    ) -> Tuple[List[Dict[str, Any]], bool]
    
    def get_metrics_snapshot(self) -> Dict[str, Any]
```

## See Also

- `reflexive_cycle_integration.py` - Integration with AutonomousMiningController
- `tests/test_reflexive_cycle_timeout.py` - Comprehensive test suite
- `autonomous_mining_controller.py` - Main mining controller
