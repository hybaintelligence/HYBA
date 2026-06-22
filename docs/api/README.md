# API Reference

## Base URL

```
http://localhost:8000/api
```

## Authentication

All security and regeneration endpoints require API key authentication via the `X-API-Key` header when `HYBA_API_KEYS` environment variable is configured.

```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/security/status
```

## Endpoints

### Security API

#### `GET /api/security/status`
Returns comprehensive security status integrating all intelligence types.

**Response**:
```json
{
  "status": "integrated",
  "timestamp": "2026-06-22T12:33:20Z",
  "intelligence_integration": {
    "consciousness_engine": {
      "phi_integrated": 0.95,
      "integration_regime": "high_coherence",
      "component_integration": 0.92
    },
    "synaptic_persistence": {
      "total_patterns": 1523,
      "total_weight": 847.3,
      "learning_rate": 0.05
    },
    "swarm_coherence": {
      "coherence_level": 0.87,
      "active_nodes": 12,
      "structural_coupling": 0.91
    },
    "quantum_regeneration": {
      "total_modules": 48,
      "modules_in_blastema": 2,
      "modules_with_positional_memory": 45
    }
  },
  "threat_level": "nominal",
  "defense_systems": {
    "stabilizer_swarm": "active",
    "hebbian_learning": "active",
    "self_healing": "active",
    "blockchain_monitoring": "active"
  }
}
```

#### `POST /api/security/regeneration/trigger`
Trigger quantum regeneration for a security module.

**Request Body**:
```json
{
  "module_id": "security_module_42",
  "clifford_index": 42,
  "ai_triggered": true,
  "dry_run": false,
  "verify_after_apply": true
}
```

**Response**:
```json
{
  "success": true,
  "status": "regeneration_triggered",
  "timestamp": "2026-06-22T12:33:20Z",
  "module_id": "security_module_42",
  "regeneration_trace": {
    "module_id": "security_module_42",
    "initial_entropy": 0.0,
    "post_fault_entropy": 0.69,
    "post_quarantine_role_probs": {
      "healthy_specialized": 0.25,
      "blastema": 0.25,
      "quarantined": 0.25,
      "redifferentiating": 0.25
    },
    "fidelity_pre_collapse": 0.85,
    "collapsed_role": "healthy_specialized",
    "status": "success",
    "final_entropy": 0.0,
    "refractory_period_end": 1719033200.0
  },
  "impact_score": 0.72,
  "files_changed": ["modules/security_module_42.py"],
  "rollback_possible": true,
  "verification_result": {
    "status": "passed",
    "overall_passed": true,
    "tests_run": [...]
  }
}
```

#### `GET /api/security/regeneration/events`
Get regeneration event log for CEO terminal.

**Query Parameters**:
- `limit` (int, default=100): Maximum number of events to return
- `include_pending` (bool, default=true): Include pending approvals

**Response**:
```json
{
  "status": "regeneration_events",
  "timestamp": "2026-06-22T12:33:20Z",
  "events": [
    {
      "id": "regen_1719032000_security_module_42",
      "timestamp": "2026-06-22T12:33:20Z",
      "module_id": "security_module_42",
      "event_type": "recovery",
      "severity": "medium",
      "status": "completed",
      "ai_triggered": true,
      "impact_score": 0.72,
      "files_changed": ["modules/security_module_42.py"],
      "rollback_possible": true,
      "approval_status": "auto_approved",
      "verification_status": "passed",
      "verification_passed": true,
      "details": {
        "trace": {...},
        "verification_result": {...}
      }
    }
  ],
  "total_events": 1523,
  "pending_approvals": [],
  "pending_count": 0
}
```

#### `POST /api/security/regeneration/approve`
Approve, reject, or edit a pending AI-triggered regeneration.

**Request Body**:
```json
{
  "event_id": "regen_1719032000_security_module_42",
  "action": "approve",
  "edited_parameters": {}
}
```

**Response**:
```json
{
  "success": true,
  "status": "regeneration_approved_and_executed",
  "timestamp": "2026-06-22T12:33:20Z",
  "event_id": "regen_1719032000_security_module_42",
  "execution_result": {...},
  "signature": "hmac_sha256_..."
}
```

#### `POST /api/security/regeneration/multi-step`
Execute multi-step regeneration using the hierarchical agent system.

**Request Body**:
```json
{
  "prompt": "Fix the authentication bypass vulnerability in the login module",
  "target_files": ["auth/login.py", "auth/middleware.py"],
  "context": {
    "severity": "high",
    "affected_services": ["api", "web"]
  },
  "auto_approve_threshold": 85.0
}
```

**Response**:
```json
{
  "success": true,
  "status": "multi_step_regeneration_completed",
  "timestamp": "2026-06-22T12:33:20Z",
  "result": {
    "regeneration_id": "multi_step_1719032000",
    "status": "success",
    "steps": [
      {
        "step": "diagnosis",
        "agent": "diagnosis_agent",
        "result": {
          "fault_type": "authentication_bypass",
          "severity": 0.85,
          "affected_files": ["auth/login.py"]
        }
      },
      {
        "step": "planning",
        "agent": "planning_agent",
        "result": {
          "strategy": "patch_and_test",
          "estimated_duration_ms": 3500
        }
      },
      {
        "step": "specialist",
        "agent": "backend_specialist",
        "result": {
          "fix_applied": true,
          "files_modified": ["auth/login.py"]
        }
      },
      {
        "step": "verification",
        "agent": "verification_specialist",
        "result": {
          "tests_passed": 12,
          "tests_failed": 0
        }
      },
      {
        "step": "execution",
        "agent": "executor_agent",
        "result": {
          "deployed": true,
          "rollback_available": true
        }
      }
    ]
  }
}
```

#### `GET /api/security/regeneration/agents/status`
Get the status of all registered agents in the multi-agent system.

**Response**:
```json
{
  "success": true,
  "timestamp": "2026-06-22T12:33:20Z",
  "orchestrator_status": {
    "registered_agents": 6,
    "active_agents": 6,
    "total_regenerations": 1523,
    "success_rate": 0.97,
    "average_duration_ms": 4200
  }
}
```

#### `GET /api/security/regeneration/swarm/status`
Get Salamander Swarm Intelligence status.

**Response**:
```json
{
  "success": true,
  "status": "swarm_intelligence_status",
  "timestamp": "2026-06-22T12:33:20Z",
  "swarm": {
    "registered_agents": 8,
    "active_proposals": 2,
    "pheromone_trails_count": 847,
    "message_history_size": 15234,
    "communication_mode": "Async + Broadcast",
    "consensus_mechanism": "Majority Vote",
    "task_allocation": "PSO-Optimized",
    "learning_rate": "5% decay/min"
  }
}
```

### WebSocket API

#### `WS /api/security/regeneration/ws`
Real-time regeneration event streaming.

**Connection**:
```javascript
const ws = new WebSocket('ws://localhost:8000/api/security/regeneration/ws?room=ceo&client_id=terminal_1');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

**Message Types**:

1. **Connection Established**:
```json
{
  "type": "connection_established",
  "room": "ceo",
  "client_id": "terminal_1",
  "timestamp": "2026-06-22T12:33:20Z"
}
```

2. **Initial State**:
```json
{
  "type": "initial_state",
  "room": "ceo",
  "client_id": "terminal_1",
  "events": [...],
  "pending_approvals": [],
  "retry_history": {},
  "timestamp": "2026-06-22T12:33:20Z"
}
```

3. **Regeneration Event**:
```json
{
  "type": "regeneration_event",
  "event": {
    "id": "regen_1719032000_security_module_42",
    "timestamp": "2026-06-22T12:33:20Z",
    "module_id": "security_module_42",
    "event_type": "recovery",
    "status": "completed",
    "ai_triggered": true
  },
  "timestamp": "2026-06-22T12:33:20Z"
}
```

4. **Heartbeat**:
```json
{
  "type": "heartbeat",
  "timestamp": "2026-06-22T12:33:20Z"
}
```

**Client Messages**:
- `ping` → Server responds with `pong`
- `subscribe:room_name` → Switch to different room (ceo, cto, dev, all)
- Any other text → Echoed back

### Organism Regeneration API

#### `GET /api/organism/regeneration/status`
Return aggregate regenerative health for the 32-lane manifold.

**Response**:
```json
{
  "system_phi": 0.94,
  "innervation_stable": true,
  "active_blastemas": 2,
  "global_fidelity_mean": 0.91,
  "regeneration_potential": "high",
  "fidelity_events": 1523,
  "lanes": [
    {
      "lane_id": 0,
      "progenitor_id": "prog_0",
      "module_id": "module_0",
      "role_probabilities": {
        "healthy_specialized": 0.95,
        "blastema": 0.02,
        "quarantined": 0.02,
        "redifferentiating": 0.01
      },
      "blastema_entropy": 0.15,
      "is_primed": true,
      "evidence_source": "quantum_formalism"
    }
  ]
}
```

#### `GET /api/organism/regeneration/blastema`
View lane progenitor templates and role-model state.

**Response**:
```json
[
  {
    "lane_id": 0,
    "progenitor_id": "prog_0",
    "module_id": "module_0",
    "role_probabilities": {...},
    "blastema_entropy": 0.15,
    "is_primed": true,
    "evidence_source": "quantum_formalism"
  }
]
```

#### `POST /api/organism/regeneration/dedifferentiate/{lane_id}`
Operator-triggered regeneration of a single search lane.

**Response**:
```json
{
  "timestamp": "2026-06-22T12:33:20Z",
  "lane_id": 0,
  "module_id": "module_0",
  "pre_injury_phi": 0.94,
  "post_recovery_fidelity": 0.92,
  "scarring_detected": false,
  "recovery_duration_ms": 4200,
  "status": "success",
  "trace": {...}
}
```

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Missing or invalid API key |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 423 | Locked - Resource in refractory period |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Regeneration failed |
| 503 | Service Unavailable - Resource limits exceeded |

## Rate Limits

- **AI-Triggered Regenerations**: 5 per 60 seconds per module
- **Concurrent Regenerations**: Maximum 5 simultaneous
- **Regeneration Duration**: Maximum 5 minutes per regeneration
- **WebSocket Connections**: Maximum 100 concurrent per room

## SDKs and Client Libraries

### Python
```bash
pip install salamander-client
```

```python
from salamander import SalamanderClient

client = SalamanderClient(api_key="your-api-key")
result = client.trigger_regeneration(
    module_id="my_module",
    clifford_index=42,
    ai_triggered=True
)
```

### JavaScript/TypeScript
```bash
npm install @salamander/client
```

```typescript
import { SalamanderClient } from '@salamander/client';

const client = new SalamanderClient({ apiKey: 'your-api-key' });
const result = await client.triggerRegeneration({
  moduleId: 'my_module',
  cliffordIndex: 42,
  aiTriggered: true
});
```

### Go
```bash
go get github.com/yourorg/salamander-go
```

```go
client := salamander.NewClient("your-api-key")
result, err := client.TriggerRegeneration(&salamander.RegenerationRequest{
    ModuleID: "my_module",
    CliffordIndex: 42,
    AITriggered: true,
})
```

## Support

- **Documentation**: https://docs.salamander.yourorg.com
- **API Status**: https://status.salamander.yourorg.com
- **Support Email**: api-support@yourorg.com
- **GitHub Issues**: https://github.com/yourorg/salamander/issues