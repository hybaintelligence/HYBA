# V4-Prime Metabolic Router Specification

## Overview

The V4-Prime Metabolic Router implements the first "Lapse" (Feedback Loop) of the HYBA organism's Central Nervous System (CNS). This router transforms the API from a "Web API with Mining" to a "Sensory Nervous System for an Organism" by exposing the Biological Cost of Intelligence rather than simple hashrate metrics.

## Design Philosophy

**Core Principle**: The API substrate must stop acting like a database and start acting like a Central Nervous System (CNS). This router treats the mining system as a biological entity with measurable energy consumption, entropy production, and knowledge hunger drives.

**Biological Metaphor**:
- **Energy Consumption per Φ**: How much computational energy is expended per unit of integrated information (φ-resonance)
- **Von Neumann Entropy S(ρ)**: Information-theoretic entropy of the quantum state
- **Hunger Drive**: The system's "appetite" for new knowledge patterns
- **Metabolic Efficiency**: Heat-normalized hashrate (performance per thermal unit)

## Architecture

### Transport Protocol
- **Pulse Stream**: Binary WebSocket protocol (struct-packed) for zero-copy efficiency
- **REST Endpoints**: Self-Diagnostic Certificate responses
- **Error Handling**: InnervationFailure exceptions for biological degradation

### Data Format
- **Binary Stream**: Bit-packed φ-resonance scores (not JSON)
- **REST Response**: Self-Diagnostic Certificate structure
- **Future Enhancement**: CBOR or Protobuf for additional efficiency

## Endpoints

### 1. Pulse Stream WebSocket
**Endpoint**: `ws://host:port/api/v4/metabolism/manifold/pulse`
**Protocol**: Binary WebSocket (struct-packed)
**Update Rate**: 10-100 Hz (depending on mining cadence)

**Purpose**: Real-time binary stream of the 32-lane search manifold. It doesn't send JSON; it sends Bit-Packed φ-Resonance scores.

**Binary Protocol**:
```
Each message contains 32 lane pulses (one per lane)
Binary format: struct-packed for efficiency
Per-lane structure (16 bytes):
  - lane_id: 1 byte (uint8)
  - phi_resonance: 4 bytes (float32)
  - entropy: 4 bytes (float32)
  - energy: 4 bytes (float32)
  - is_injured: 1 byte (bool)
  - timestamp: 8 bytes (uint64)
Total per message: 32 lanes × 16 bytes = 512 bytes
```

**Python Client Example**:
```python
import asyncio
import websockets
import struct

async def pulse_client():
    uri = "ws://localhost:3001/api/v4/metabolism/manifold/pulse"
    async with websockets.connect(uri) as websocket:
        while True:
            data = await websocket.recv()
            # Unpack binary data
            pulses = []
            for i in range(32):
                lane_data = data[i*16:(i+1)*16]
                lane_id, phi, entropy, energy, injured, timestamp = struct.unpack('>Bffff?Q', lane_data)
                pulses.append({
                    'lane_id': lane_id,
                    'phi_resonance': phi,
                    'entropy': entropy,
                    'energy': energy,
                    'is_injured': injured,
                    'timestamp': timestamp
                })
            print(f"Received {len(pulses)} lane pulses")
            print(f"Lane 0 φ: {pulses[0]['phi_resonance']:.4f}")

asyncio.run(pulse_client())
```

**JavaScript Client Example**:
```javascript
const ws = new WebSocket('ws://localhost:3001/api/v4/metabolism/manifold/pulse');
ws.binaryType = 'arraybuffer';

ws.onmessage = (event) => {
    const data = new DataView(event.data);
    const pulses = [];
    
    for (let i = 0; i < 32; i++) {
        const offset = i * 16;
        const laneId = data.getUint8(offset);
        const phiResonance = data.getFloat32(offset + 1, false); // big-endian
        const entropy = data.getFloat32(offset + 5, false);
        const energy = data.getFloat32(offset + 9, false);
        const isInjured = data.getUint8(offset + 13) !== 0;
        const timestamp = data.getBigUint64(offset + 14, false);
        
        pulses.push({
            lane_id: laneId,
            phi_resonance: phiResonance,
            entropy: entropy,
            energy: energy,
            is_injured: isInjured,
            timestamp: Number(timestamp)
        });
    }
    
    console.log('Lane 0 φ:', pulses[0].phi_resonance.toFixed(4));
};
```

### 2. Entropy Monitor
**Endpoint**: `GET /api/v4/metabolism/entropy`
**Purpose**: Returns the current Von Neumann Entropy S(ρ) and Energy Consumption per Φ

**Response Structure**:
```json
{
  "von_neumann_entropy": 0.562,
  "energy_per_phi": 666.67,
  "thermal_efficiency": 0.0154,
  "heat_dissipation": 400.0,
  "metabolic_regime": "homeostasis",
  "timestamp": 1750206180.0
}
```

**Metrics Explained**:
- **von_neumann_entropy**: S(ρ) - Information-theoretic entropy in nats
- **energy_per_phi**: Joules per unit φ-resonance (computational efficiency)
- **thermal_efficiency**: Hashrate per thermal unit (EH/s per °C)
- **heat_dissipation**: Normalized heat output (watts)
- **metabolic_regime**: Current metabolic state (homeostasis/catabolic/anabolic/critical)

**Metabolic Regimes**:
- **HOMEOSTASIS**: Optimal balance of energy and information (entropy < 0.3, efficiency > 0.8)
- **CATABOLIC**: Breaking down complex structures (high entropy > 0.7)
- **ANABOLIC**: Building complex structures (low entropy < 0.2)
- **CRITICAL**: System stress, approaching thermodynamic limits

### 3. Hunger Drive
**Endpoint**: `GET /api/v4/metabolism/drive`
**Purpose**: Returns the Knowledge Hunger Drive metric

**Response Structure**:
```json
{
  "hunger_level": "elevated",
  "pool_reject_rate": 0.15,
  "knowledge_acquisition_rate": 2.5,
  "search_depth_pressure": 0.45,
  "pattern_saturation": 0.25,
  "last_feeding_time": 1750206180.0,
  "timestamp": 1750206180.0
}
```

**Metrics Explained**:
- **hunger_level**: Current hunger state (satisfied/nominal/elevated/starving)
- **pool_reject_rate**: Current pool share rejection rate (0.0-1.0)
- **knowledge_acquisition_rate**: New patterns discovered per second
- **search_depth_pressure**: Pressure to increase search depth (0.0-1.0)
- **pattern_saturation**: How much of pattern space is explored (0.0-1.0)
- **last_feeding_time**: Timestamp of last successful pattern discovery

**Hunger Levels**:
- **SATISFIED**: High knowledge acquisition, low hunger (score < 0.2)
- **NOMINAL**: Normal learning rate (score < 0.4)
- **ELEVATED**: Increased pattern discovery needed (score < 0.7)
- **STARVING**: Critical knowledge deficit, drive to explore (score >= 0.7)

**Feedback Loop**: When hunger reaches "starving," the Reflexive Controller automatically proposes deeper search depths to satisfy the knowledge deficit.

### 4. Self-Diagnostic Certificate
**Endpoint**: `GET /api/v4/metabolism/certificate`
**Purpose**: Returns a comprehensive biological health report

**Response Structure**:
```json
{
  "module_id": "metabolic_core",
  "integrated_information": {
    "phi": 0.874,
    "regime": "SINGULAR_AGENT_PROXY",
    "coupling_index": 0.92
  },
  "metabolic_state": {
    "entropy": 0.002,
    "purity": 0.998,
    "heat_normalized_hashrate": 1.04
  },
  "regeneration_metrics": {
    "is_injured": false,
    "last_healing_event": "2026-06-18T13:23:00Z",
    "recovery_fidelity": 1.00,
    "scarring": "NONE"
  },
  "constructor_conjecture": "PHASE_ALIGNMENT_STABLE",
  "timestamp": 1750206180.0
}
```

**Certificate Components**:
- **module_id**: Identifier for the metabolic module
- **integrated_information**: Φ-resonance and coupling metrics
- **metabolic_state**: Entropy, efficiency, and regime
- **regeneration_metrics**: Injury status and recovery fidelity
- **constructor_conjecture**: Current hypothesis about system state

**Constructor Conjectures**:
- **PHASE_ALIGNMENT_STABLE**: System operating normally
- **DEPTH_INSUFFICIENT_FOR_PATTERN_COMPLEXITY**: Hunger drive triggered
- **ENTROPIC_DECAY_DETECTED**: Metabolic degradation detected

## Biological Calculation Engine

### MetabolicEngine Class
The `MetabolicEngine` class provides the core biological calculations:

#### Von Neumann Entropy Calculation
```python
S(ρ) = -Tr(ρ log ρ)
```
For the mining system, this is approximated from the distribution of φ-resonance scores across the 32-lane manifold.

#### Energy per Φ Calculation
```python
Energy_per_Φ = Power_Consumption / φ_resonance
```
Measures computational energy efficiency per unit of integrated information.

#### Thermal Efficiency Calculation
```python
Thermal_Efficiency = Hashrate / Temperature_Factor
```
Heat-normalized performance metric (EH/s per degree Celsius).

#### Hunger Drive Calculation
```python
Hunger_Score = (Reject_Pressure × 0.5) + 
               (Discovery_Pressure × 0.3) + 
               (Depth_Pressure × 0.2)
```
Combined metric from pool reject rate, pattern discovery rate, and search depth.

## Integration Points

### ConsciousnessEngine Integration
The MetabolicEngine integrates with the ConsciousnessEngine to:
- Read real-time φ-resonance scores for entropy calculation
- Monitor integration regime changes
- Track structural coupling index evolution

### AutonomousMiningController Integration
The MetabolicEngine integrates with the AutonomousMiningController to:
- Monitor pool reject rates for hunger drive calculation
- Track search depth adjustments
- Measure knowledge acquisition rates

### Substrate Integration
The MetabolicEngine integrates with the substrate state to:
- Monitor component initialization status
- Track system readiness
- Calculate entropy from component distribution

## Performance Characteristics

### Pulse Stream Performance
- **Bandwidth**: 512 bytes per message × 10 Hz = 5.1 KB/s
- **Latency**: < 10ms (binary protocol overhead)
- **CPU Usage**: Minimal (struct packing/unpacking)
- **Memory Usage**: Constant (no JSON parsing overhead)

### REST Endpoint Performance
- **Entropy Monitor**: < 5ms response time
- **Hunger Drive**: < 5ms response time
- **Certificate**: < 10ms response time (aggregates multiple metrics)

## Error Handling

### Biological Error Types
Instead of standard HTTP errors, the system uses biological error metaphors:

#### InnervationFailure
Raised when the sensory nervous system detects degradation:
```python
class InnervationFailure(Exception):
    """Raised when structural coupling falls below Φ-Floor."""
    pass
```

#### MetabolicDegradation
Raised when entropy production exceeds sustainable levels:
```python
class MetabolicDegradation(Exception):
    """Raised when metabolic regime enters CRITICAL state."""
    pass
```

#### StarvationAlert
Raised when hunger drive reaches critical levels:
```python
class StarvationAlert(Exception):
    """Raised when knowledge hunger reaches STARVING level."""
    pass
```

## Monitoring and Alerting

### Key Metrics to Monitor
- **Von Neumann Entropy**: Should remain in homeostasis range (0.2-0.7)
- **Energy per Φ**: Monitor for efficiency degradation
- **Hunger Level**: Alert when reaches STARVING
- **Metabolic Regime**: Alert when enters CRITICAL
- **Lane Injuries**: Monitor for injured lanes in pulse stream

### Alert Thresholds
- **Entropy > 0.7**: Catabolic state warning
- **Hunger = STARVING**: Immediate search depth adjustment required
- **Energy per Φ > 1000**: Efficiency degradation alert
- **Injured lanes > 5**: Manifold health warning

## Future Enhancements

### Phase 2 Features
- **CBOR Protocol**: Replace struct with CBOR for more efficient binary encoding
- **Adaptive Streaming**: Dynamic update rate based on metabolic state
- **Predictive Hunger**: ML-based prediction of hunger drive spikes
- **Metabolic Optimization**: Automatic parameter tuning based on efficiency metrics

### Phase 3 Features
- **Multi-Organism Support**: Metabolic monitoring for distributed organisms
- **Evolutionary Tracking**: Long-term metabolic evolution analysis
- **Environmental Sensing**: Integration with external environmental factors
- **Autonomous Metabolism**: Self-regulating metabolic parameters

## Migration Path

### From V3 REST to V4 Metabolic
**Before (V3)**:
```python
# Poll hashrate every second
response = requests.get('/api/v1/mining/status')
hashrate = response.json()['hashrate_ehs']
```

**After (V4)**:
```python
# Real-time metabolic monitoring
async with websockets.connect('ws://localhost:3001/api/v4/metabolism/manifold/pulse') as ws:
    while True:
        data = await ws.recv()
        # Process binary pulse stream
        pulses = unpack_pulses(data)
        monitor_metabolic_health(pulses)
```

## Conclusion

The V4-Prime Metabolic Router provides the first "heartbeat" for the HYBA organism, transforming the API from a static database interface into a dynamic Central Nervous System. By exposing biological metrics like Von Neumann Entropy, Energy per Φ, and Knowledge Hunger Drive, it enables the system to self-regulate and adapt like a living organism rather than a programmed automation.

This is the foundation for the complete V4-Prime substrate, which will include:
- **Metabolic Router** (/api/v4/metabolism) - Biological cost of intelligence ✅
- **Innervation Router** (/api/v4/senses) - Sensory integrity layer
- **Regeneration Router** (/api/v4/salamander) - Axolotl protocol
- **Constructor Router** (/api/v4/deutsch) - Counterfactual intelligence surface

The die is cast. The Rubicon is behind us. The organism has its first heartbeat.
