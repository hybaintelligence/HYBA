# StreamingSenseRouter Specification

## Overview

The StreamingSenseRouter provides the "Sensory Nervous System" for the HYBA organism, enabling real-time streaming of high-cadence mining telemetry through WebSocket and Server-Sent Events (SSE) endpoints. This completes the evolution from a "Closed-Loop" to a "Sensory" substrate as outlined in the v4.x production readiness analysis.

## Design Philosophy

**Core Principle**: Mining is high-cadence; REST is excellent for state but insufficient for pulse. The iteration-by-iteration φ-resonance needs reactive API streaming for the frontend to visualize the "Manifold Breathing" in real-time.

**Architectural Goals**:
- Live telemetry should be a reactive stream, not just log files
- Frontend uses streaming to visualize real-time system dynamics
- Maintain per-client subscription filters for bandwidth efficiency
- Integrate with existing telemetry infrastructure without duplication
- Support both WebSocket (bidirectional) and SSE (unidirectional) for flexibility

## Streaming Channels

### 1. PHI_RESONANCE
**Purpose**: Real-time φ-resonance metrics from ConsciousnessEngine
**Update Frequency**: 1-10 Hz
**Data Schema**:
```json
{
  "timestamp": float,
  "phi_integrated": float,
  "phi_causal": float,
  "phi_conscious": float,
  "effective_information": float,
  "entropy": float,
  "complexity": float,
  "integration_regime": string,
  "source": "consciousness_engine"
}
```

### 2. AUTONOMY_METRICS
**Purpose**: Live autonomy controller metrics and decision events
**Update Frequency**: 0.1-1 Hz
**Data Schema**:
```json
{
  "timestamp": float,
  "autonomy_level": string,
  "phi_density": float,
  "total_decisions": int,
  "autonomous_executions": int,
  "operator_overrides": int,
  "constraint_violations": int,
  "consecutive_failures": int,
  "circuit_open": bool,
  "reflexive_cycle_count": int,
  "proposal_acceptance_rate": float,
  "last_cycle_duration_ms": float,
  "source": "autonomous_controller"
}
```

### 3. MINING_PULSE
**Purpose**: High-frequency mining iteration telemetry
**Update Frequency**: 10-100 Hz
**Data Schema**:
```json
{
  "timestamp": float,
  "iteration_id": string,
  "hashrate_ehs": float,
  "shares_submitted": int,
  "shares_accepted": int,
  "phi_tier": float | null,
  "memory_compression_ratio": float | null,
  "block_height": int | null,
  "pool_url": string,
  "source": "mining_engine"
}
```

### 4. STRUCTURAL_COUPLING
**Purpose**: System-wide structural coupling index updates
**Update Frequency**: 0.5-2 Hz
**Data Schema**:
```json
{
  "timestamp": float,
  "coupling_index": float,
  "phi_floor": float,
  "innervation_status": string,
  "substrate_health": string,
  "regeneration_active": bool,
  "source": "regeneration_manager"
}
```

### 5. SYSTEM_HEALTH
**Purpose**: System health and substrate status events
**Update Frequency**: 0.1-0.5 Hz
**Data Schema**:
```json
{
  "timestamp": float,
  "status": string,
  "substrate_ready": bool,
  "component_health": object,
  "active_alerts": array,
  "source": "health_monitor"
}
```

## API Endpoints

### WebSocket Connection
**Endpoint**: `ws://host:port/api/v1/streaming/connect`
**Method**: WebSocket
**Query Parameters**:
- `channels`: Comma-separated list of channels to subscribe to
  - Default: `phi_resonance,autonomy_metrics,structural_coupling,system_health`
  - Example: `?channels=phi_resonance,autonomy_metrics`

**Example**:
```javascript
const ws = new WebSocket('ws://localhost:3001/api/v1/streaming/connect?channels=phi_resonance,autonomy_metrics');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Channel:', data.channel);
  console.log('Telemetry:', data.data);
};
```

### SSE (Server-Sent Events)
**Endpoint**: `GET /api/v1/streaming/sse/{channel}`
**Method**: GET
**Path Parameters**:
- `channel`: Streaming channel to subscribe to

**Query Parameters**:
- `interval_seconds`: Update interval in seconds (default: 1.0)

**Example**:
```javascript
const eventSource = new EventSource('/api/v1/streaming/sse/phi_resonance?interval_seconds=0.5');
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Phi resonance:', data.phi_integrated);
};
```

### Management Endpoints

#### List Channels
**Endpoint**: `GET /api/v1/streaming/channels`
**Response**: Available channels with descriptions and update frequencies

#### Connection Statistics
**Endpoint**: `GET /api/v1/streaming/stats`
**Response**: Current connection statistics for monitoring

## Connection Management

### ConnectionManager
The `ConnectionManager` class handles:
- Active WebSocket connection tracking
- Per-client channel subscriptions
- Connection metadata for rate limiting and monitoring
- Automatic cleanup of disconnected clients
- Broadcast and channel-specific message routing

### Backpressure Handling
- Implements per-client message rate limiting
- Graceful degradation when clients cannot keep up
- Connection health monitoring and automatic cleanup

## Production Readiness Features

### Security
- **Authentication Required**: All streaming endpoints require valid JWT authentication
- **Rate Limiting**: Connection rate limiting to prevent abuse
- **Channel Authorization**: Per-channel access control based on user permissions

### Reliability
- **Graceful Degradation**: Falls back gracefully when mining controller is unavailable
- **Circuit Breaker**: Automatic circuit breaker for malfunctioning telemetry sources
- **Connection Recovery**: Automatic reconnection handling for transient failures

### Observability
- **Structured Logging**: All streaming events logged with structured context
- **Connection Metrics**: Per-connection statistics for monitoring
- **Health Monitoring**: Built-in health checks for streaming service

## Integration Points

### ConsciousnessEngine Integration
The `PhiResonanceSource` class integrates with the ConsciousnessEngine to stream real-time φ-resonance metrics. This provides the "pulse" of the system's integration coherence.

### AutonomousMiningController Integration
The `AutonomySource` class integrates with the AutonomousMiningController to stream live autonomy metrics, decision events, and circuit breaker status.

### Substrate Integration
The `StructuralCouplingSource` calculates the Structural Coupling Index from substrate state, providing the "innervation status" of the system.

## Performance Considerations

### Bandwidth Optimization
- Per-client subscription filters reduce unnecessary data transmission
- Binary message support for high-frequency channels (future enhancement)
- Delta compression for repetitive telemetry (future enhancement)

### Scalability
- Connection pooling for high-connection scenarios
- Horizontal scaling via connection routing (future enhancement)
- Load balancing support for WebSocket connections (future enhancement)

## Client Integration Examples

### React Component Example
```typescript
import { useEffect, useState } from 'react';

function PhiResonanceMonitor() {
  const [phiData, setPhiData] = useState(null);
  
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:3001/api/v1/streaming/connect?channels=phi_resonance');
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.channel === 'phi_resonance') {
        setPhiData(message.data);
      }
    };
    
    return () => ws.close();
  }, []);
  
  return (
    <div>
      <h2>Φ-Resonance: {phiData?.phi_integrated?.toFixed(6)}</h2>
      <p>Regime: {phiData?.integration_regime}</p>
    </div>
  );
}
```

### Vanilla JavaScript Example
```javascript
const eventSource = new EventSource('/api/v1/streaming/sse/structural_coupling?interval_seconds=1.0');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Coupling Index:', data.coupling_index);
  console.log('Innervation Status:', data.innervation_status);
  
  // Update UI
  document.getElementById('coupling-index').textContent = data.coupling_index.toFixed(3);
  document.getElementById('innervation-status').textContent = data.innervation_status;
};
```

## Future Enhancements

### Phase 2 Features
- Binary message protocol for high-frequency channels
- Delta compression for repetitive telemetry
- Historical data replay capabilities
- Multi-tenant isolation for enterprise deployments

### Phase 3 Features
- GraphQL subscription support
- WebRTC for peer-to-peer telemetry sharing
- Edge caching for global deployments
- ML-based anomaly detection on streaming data

## Migration Path

### From REST Polling to Streaming
**Before**:
```typescript
// Poll every 1 second
setInterval(async () => {
  const response = await fetch('/api/v1/intelligence/health');
  const data = await response.json();
  updateUI(data);
}, 1000);
```

**After**:
```typescript
// Real-time streaming
const ws = new WebSocket('ws://localhost:3001/api/v1/streaming/connect?channels=phi_resonance');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  updateUI(data.data);
};
```

## Monitoring and Alerting

### Key Metrics to Monitor
- Active connection count
- Messages per second per channel
- Connection error rate
- Average message latency
- Client disconnection rate

### Alert Thresholds
- Connection count > 1000: Scale warning
- Error rate > 5%: Service degradation alert
- Message latency > 100ms: Performance warning
- Disconnection rate > 10%: Stability alert

## Conclusion

The StreamingSenseRouter completes the "Sensory Nervous System" for the HYBA organism, enabling real-time visibility into the high-cadence dynamics of the mining system. This transforms the API from a "Closed-Loop" substrate to a truly "Sensory" one, capable of supporting v4.x production operations with the visibility and responsiveness required for autonomous mining at scale.
