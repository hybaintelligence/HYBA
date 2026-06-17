# Operator Approval Protocol

## Purpose

The Operator Approval Protocol defines the interaction contract for human-in-the-loop governance in the HYBA autonomous mining system. This protocol maps out the state-machine rules for how SUPERVISED operations transition into a pending request pool, the strict τ_timeout duration parameters, the structure of the OperatorApprovalDecision object, and the fail-closed terminal state logic.

## State Machine Overview

### Autonomy Levels

```
ADVISORY → SUPERVISED → AUTONOMOUS
```

#### ADVISORY Mode
- System generates recommendations only
- No autonomous execution without explicit approval
- All actions require operator sign-off
- τ_timeout: 300 seconds (5 minutes)

#### SUPERVISED Mode
- System can execute within defined safety boundaries
- High-impact actions require approval
- Routine operations proceed autonomously
- τ_timeout: 600 seconds (10 minutes)

#### AUTONOMOUS Mode
- Full autonomous operation within mission parameters
- Emergency interventions only
- Circuit breaker always active
- τ_timeout: 120 seconds (2 minutes for emergency override)

## Approval Request Structure

### OperatorApprovalDecision Object

```json
{
  "request_id": "string (UUID v4)",
  "timestamp": "ISO8601",
  "autonomy_level": "advisory|supervised|autonomous",
  "action_type": "mining_operation|parameter_change|emergency_stop",
  "priority": "low|medium|high|critical",
  "content": {
    "decision_id": "string",
    "phi_density": "float",
    "compression_ratio": "float",
    "hashrate_scaling": "float",
    "target_pool": "string",
    "estimated_impact": "string"
  },
  "tau_timeout_seconds": "integer",
  "expires_at": "ISO8601",
  "approval_status": "pending|approved|rejected|expired",
  "operator_id": "string",
  "justification": "string",
  "evidence_seal_id": "string"
}
```

### Field Specifications

#### request_id
- **Type**: UUID v4 string
- **Purpose**: Unique identifier for approval request
- **Generation**: System-generated on request creation

#### timestamp
- **Type**: ISO8601 datetime string
- **Purpose**: Moment when request was created
- **Format**: `YYYY-MM-DDTHH:MM:SS.sssZ`

#### autonomy_level
- **Type**: enum string
- **Values**: `advisory`, `supervised`, `autonomous`
- **Purpose**: Current system autonomy level

#### action_type
- **Type**: enum string
- **Values**: 
  - `mining_operation`: Mining pool connection, share submission
  - `parameter_change`: System parameter modification
  - `emergency_stop`: Immediate system halt
- **Purpose**: Category of action requiring approval

#### priority
- **Type**: enum string
- **Values**: `low`, `medium`, `high`, `critical`
- **Purpose**: Urgency level for approval processing

#### content
- **Type**: object (varies by action_type)
- **Purpose**: Detailed information about the proposed action

#### tau_timeout_seconds
- **Type**: integer
- **Purpose**: Maximum time allowed for operator response
- **Values**:
  - ADVISORY: 300 seconds
  - SUPERVISED: 600 seconds
  - AUTONOMOUS: 120 seconds (emergency only)

#### expires_at
- **Type**: ISO8601 datetime string
- **Purpose**: Calculated expiration time
- **Formula**: `timestamp + tau_timeout_seconds`

#### approval_status
- **Type**: enum string
- **Values**: 
  - `pending`: Awaiting operator decision
  - `approved`: Operator granted approval
  - `rejected`: Operator denied approval
  - `expired`: Timeout reached without decision

#### operator_id
- **Type**: string
- **Purpose**: Identifier of operator making decision
- **Required**: For approved/rejected status

#### justification
- **Type**: string
- **Purpose**: Reason for approval/rejection decision
- **Required**: For approved/rejected status

#### evidence_seal_id
- **Type**: string
- **Purpose**: Link to evidence seal for audit trail
- **Generated**: On final decision

## Request Pool Management

### Pending Request Pool

Location: `artifacts/operator_approvals/pending/`

Structure:
- Individual JSON files named `{request_id}.json`
- Index file: `artifacts/operator_approvals/pending_index.json`

### Processing Rules

1. **FIFO Processing**: Requests processed in order of creation
2. **Priority Override**: Critical requests jump queue
3. **Timeout Handling**: Expired requests moved to rejected pool
4. **Concurrency**: Maximum 5 concurrent pending requests per operator

### State Transitions

```
PENDING → APPROVED → EXECUTED
PENDING → REJECTED → ARCHIVED
PENDING → EXPIRED → ARCHIVED
```

## Fail-Closed Terminal State Logic

### Circuit Breaker Triggers

1. **Boundary Violation**: φ-density > 0.95, compression_ratio > 1.95
2. **Operator Override**: Explicit emergency stop request
3. **Timeout Cascade**: 3 consecutive approval timeouts
4. **System Anomaly**: Unexpected error rate > 5% over 10 minutes

### Terminal State Behavior

When circuit breaker triggers:
1. Immediate halt of all autonomous operations
2. Transition to ADVISORY mode
3. Require explicit operator approval to resume
4. Generate evidence seal for trigger event
5. Alert all registered operators

### Recovery Procedure

1. Operator reviews trigger evidence
2. System diagnostic run
3. Parameter adjustment if needed
4. Explicit approval to exit terminal state
5. Gradual autonomy restoration (ADVISORY → SUPERVISED → AUTONOMOUS)

## Operator Authentication

### Credential Requirements

- Username: Valid operator account
- Password: Argon2id encoded hash
- Role: Approved production role (ceo, treasury_admin, mining_operator)

### Session Management

- Session timeout: 3600 seconds (1 hour)
- Multi-factor authentication required for critical actions
- Audit log of all authentication events

## Approval Interface

### API Endpoints

```
POST   /api/operator/approvals/request
GET    /api/operator/approvals/pending
POST   /api/operator/approvals/{request_id}/approve
POST   /api/operator/approvals/{request_id}/reject
GET    /api/operator/approvals/history
```

### Response Format

```json
{
  "status": "success|error",
  "request_id": "string",
  "approval_status": "pending|approved|rejected|expired",
  "timestamp": "ISO8601",
  "evidence_seal_id": "string",
  "next_steps": ["array of strings"]
}
```

## Compliance Requirements

### Audit Trail
- All approval decisions must be logged
- Evidence seals must be generated for each decision
- Logs must be retained for minimum 7 years

### Access Control
- Only approved operators can make approval decisions
- Role-based access control enforced
- Emergency override requires multi-operator consensus

### Monitoring
- Real-time monitoring of pending approval queue
- Alerts for critical requests nearing timeout
- Dashboard for approval metrics and trends

## Security Considerations

1. **Authentication**: Strong operator authentication required
2. **Authorization**: Role-based access control
3. **Integrity**: Evidence seals prevent tampering
4. **Availability**: Redundant approval processing infrastructure
5. **Confidentiality**: Sensitive operational data encrypted at rest
