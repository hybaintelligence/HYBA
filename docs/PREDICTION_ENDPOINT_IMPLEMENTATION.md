# Prediction Endpoint Implementation

## Overview

The `/api/predict` endpoint provides AI-driven mining strategy and power scale recommendations based on live optimizer measurements. This endpoint follows the repository's production discipline: it fails closed when the optimizer runtime is unavailable rather than fabricating predictions.

## Implementation Status

✅ **COMPLETE** - Prediction endpoint is fully implemented and tested

## Architecture

### Service Integration

The prediction endpoint integrates with the PYTHIA mining system's AI optimizer through the `GenesisAIServiceRegistry`:

```
┌─────────────────┐
│  /api/predict   │
│    endpoint     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ GenesisAIServiceRegistry│
└────────┬────────────────┘
         │
         ▼
┌──────────────┐      ┌────────────────┐
│  GenesisAI   │─────▶│  AIOptimizer   │
│   instance   │      │   instance     │
└──────────────┘      └────────────────┘
```

### Operational States

The endpoint has two valid operational states:

1. **Optimizer Connected** (HTTP 200)
   - Returns strategy and power scale recommendations
   - Includes confidence scores and optimizer state metrics
   - Based on measured acceptance rates and meta-learning snapshots

2. **Optimizer Unavailable** (HTTP 503)
   - Returns explicit error explaining the missing dependency
   - Fails closed to avoid fabricating ungrounded predictions
   - Indicates degraded mode without generating false confidence

## API Specification

### Request

```http
POST /api/predict
Content-Type: application/json

{
  "state": {
    "networkDifficulty": 7234567890123
  }
}
```

### Response (Optimizer Connected)

```json
{
  "success": true,
  "status": "predicted",
  "timestamp": "2026-06-15T19:00:00.000Z",
  "source": "measured_optimizer_runtime",
  "networkDifficulty": 7234567890123,
  "recommendation": {
    "strategy": "phi_scaled_compressed_solver_search",
    "power_scale": 1.0,
    "confidence": 0.85
  },
  "optimizer_state": {
    "acceptance_rate": 0.75,
    "strategy_probabilities": {
      "phi_scaled_compressed_solver_search": 0.7,
      "golden_ratio_baseline": 0.3
    },
    "recent_performance_samples": 10
  }
}
```

### Response (Optimizer Unavailable)

```http
HTTP/1.1 503 Service Unavailable
Content-Type: application/json

{
  "detail": {
    "error": "optimizer_runtime_not_connected",
    "message": "No measured optimizer runtime is connected; prediction was not generated.",
    "networkDifficulty": 7234567890123,
    "timestamp": "2026-06-15T19:00:00.000Z"
  }
}
```

## Recommendation Logic

### Power Scale Calculation

The endpoint derives power scale recommendations from recent share acceptance rates:

- **High acceptance (>70%)**: `power_scale = 1.0` (stable operation)
- **Medium acceptance (40-70%)**: `power_scale = 1.1` (slight increase)
- **Low acceptance (<40%)**: `power_scale = 1.2` (increase exploration)

### Strategy Selection

The recommended strategy is determined by:
1. Query meta-learning optimizer for strategy probabilities
2. Select strategy with highest probability (softmax-weighted)
3. Default to `phi_scaled_compressed_solver_search` if no history

### Confidence Calculation

Confidence is derived from strategy probability entropy:
- Higher entropy (uncertain distribution) → lower confidence
- Lower entropy (concentrated distribution) → higher confidence
- Formula: `confidence = 1.0 - (entropy / max_entropy)`

## Testing

### Unit Tests

Location: `tests/test_prediction_endpoint.py`

Coverage:
- ✅ 503 response when optimizer unavailable
- ✅ 200 response with recommendations when optimizer connected
- ✅ Power scale adjustment based on acceptance rate
- ✅ Invalid network difficulty validation
- ✅ Empty strategy probability handling
- ✅ Timestamp inclusion in all responses

### E2E Tests

Location: `scripts/run_backend_e2e.py`

The E2E test validates:
- Endpoint accepts valid requests
- 503 is treated as valid degraded state (not a failure)
- Request validation rejects negative/zero difficulty
- Response structure matches specification

## Production Considerations

### Fail-Closed Philosophy

The endpoint follows the repository's production discipline:

> "Power recommendations are operational controls. Returning a heuristic when the optimizer is unavailable would look like a successful prediction while being unrelated to measured activity, so the API reports the missing dependency explicitly instead of fabricating confidence or a power scale."

### Deployment Sequence

1. **Development/Testing**: Endpoint returns 503 (optimizer not started)
2. **Local Production**: GenesisAI starts and registers optimizer
3. **Live Mining**: Endpoint returns predictions based on live measurements

### Integration Points

The prediction endpoint becomes operational when:
- `GenesisAI` instance is started
- `AIOptimizer` is instantiated within GenesisAI
- `GenesisAIServiceRegistry.register_instance()` is called
- Mining loop begins accumulating performance history

## Files Modified

1. **`python_backend/pythia_mining/genesis_ai_service.py`**
   - Added `get_ai_optimizer()` class method
   - Returns AIOptimizer instance from registered GenesisAI

2. **`python_backend/hyba_genesis_api/api/misc.py`**
   - Implemented prediction logic in `predict_params()`
   - Queries optimizer meta-learning snapshot
   - Calculates recommendations from measured state

3. **`scripts/run_backend_e2e.py`**
   - Updated validation to accept 503 as valid degraded state
   - Prediction validation checks for either success or valid 503 response

4. **`tests/test_prediction_endpoint.py`** (new)
   - Comprehensive unit test coverage
   - Mocked optimizer integration tests
   - Response structure validation

## Future Enhancements

Potential improvements for future iterations:

1. **Feature-Conditioned Selection**: Use job features in strategy selection
2. **Historical Performance Windows**: Configurable acceptance rate window sizes
3. **Multi-Objective Optimization**: Balance power, thermal, and acceptance metrics
4. **Prediction Confidence Bounds**: Return confidence intervals
5. **Strategy Exploration**: Epsilon-greedy or Thompson sampling for exploration

## References

- AIOptimizer implementation: `python_backend/pythia_mining/ai_optimizer.py`
- Meta-learning optimizer: `python_backend/pythia_mining/ai_optimizer_meta.py`
- GenesisAI orchestrator: `python_backend/pythia_mining/genesis_ai.py`
- Production readiness: `docs/PRODUCTION_READINESS.md`
