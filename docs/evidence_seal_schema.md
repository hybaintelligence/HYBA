# Evidence Seal Schema

## Purpose

The Evidence Seal Schema defines the formal structure for immutability blocks that cryptographically seal autonomous decisions, mathematical parameters, and operator actions to disk. This creates an unalterable audit log for external compliance and forensic review.

## Schema Definition

### Evidence Block Structure

```json
{
  "seal_id": "string",
  "timestamp": "ISO8601",
  "block_hash": "SHA256d",
  "previous_seal": "SHA256d",
  "evidence_type": "decision|parameter|operator_action",
  "content": {
    "decision_id": "string",
    "phi_density": "float",
    "matrix_transformation": "array",
    "operator_id": "string",
    "action_type": "string",
    "approval_status": "pending|approved|rejected"
  },
  "signature": "Ed25519",
  "merkle_root": "SHA256d"
}
```

### Field Specifications

#### seal_id
- **Type**: string (UUID v4)
- **Purpose**: Unique identifier for the evidence block
- **Format**: `xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx`

#### timestamp
- **Type**: ISO8601 datetime string
- **Purpose**: Exact moment of evidence creation
- **Format**: `YYYY-MM-DDTHH:MM:SS.sssZ`

#### block_hash
- **Type**: SHA256d hash (64 hex characters)
- **Purpose**: Cryptographic fingerprint of the entire block
- **Calculation**: `SHA256d(SHA256d(block_content_without_hash))`

#### previous_seal
- **Type**: SHA256d hash (64 hex characters)
- **Purpose**: Links to previous evidence block in chain
- **Value**: `0000000000000000000000000000000000000000000000000000000000000000` for genesis block

#### evidence_type
- **Type**: enum string
- **Values**: 
  - `decision`: Autonomous system decision
  - `parameter`: Mathematical parameter change
  - `operator_action`: Human operator intervention

#### content
- **Type**: object (varies by evidence_type)

##### Decision Content
```json
{
  "decision_id": "string",
  "autonomy_level": "advisory|supervised|autonomous",
  "phi_density": "float (0.0-1.0)",
  "compression_ratio": "float (1.0-2.0)",
  "hashrate_scaling": "float (0.0-2.0)",
  "circuit_breaker_triggered": "boolean",
  "reflexive_loop_state": "string"
}
```

##### Parameter Content
```json
{
  "parameter_name": "string",
  "previous_value": "any",
  "new_value": "any",
  "change_reason": "string",
  "validation_status": "valid|invalid|pending"
}
```

##### Operator Action Content
```json
{
  "operator_id": "string",
  "action_type": "approve|reject|override|emergency_stop",
  "target_decision_id": "string",
  "approval_status": "pending|approved|rejected",
  "justification": "string",
  "tau_timeout_seconds": "integer"
}
```

#### signature
- **Type**: Ed25519 signature (128 hex characters)
- **Purpose**: Cryptographic proof of authenticity
- **Signing**: Private key of autonomous system or operator

#### merkle_root
- **Type**: SHA256d hash (64 hex characters)
- **Purpose**: Root of Merkle tree for batch verification
- **Calculation**: Merkle root of all evidence blocks in current batch

## Chain Structure

Evidence blocks form an immutable chain:

```
Genesis Block (seal_0)
    ↓ previous_seal
Block 1 (seal_1)
    ↓ previous_seal
Block 2 (seal_2)
    ↓ previous_seal
...
Block N (seal_n)
```

## Validation Rules

1. **Hash Integrity**: `block_hash` must match calculated hash of content
2. **Chain Continuity**: `previous_seal` must match actual previous block's hash
3. **Signature Validity**: `signature` must verify against known public keys
4. **Timestamp Ordering**: Timestamps must be monotonically increasing
5. **Type Consistency**: Content structure must match `evidence_type`

## Storage Format

Evidence seals are stored in:
- **Primary**: `artifacts/evidence_seals/` directory
- **Format**: Individual JSON files named `{seal_id}.json`
- **Index**: `artifacts/evidence_seals/chain_index.json` for fast lookup

## Compliance Requirements

### Forensic Review
- All evidence blocks must be retained for minimum 7 years
- Chain integrity must be verifiable at any point
- Signature verification must use auditable public keys

### External Audit
- Merkle proofs must be provided for any evidence block
- Chain index must include all seal IDs and timestamps
- Backup copies must be stored in separate geographic locations

## Security Considerations

1. **Key Management**: Ed25519 keys must be stored in HSM or equivalent
2. **Access Control**: Write access to evidence directory requires operator approval
3. **Tamper Detection**: Any modification invalidates entire chain from that point
4. **Backup Strategy**: Immutable storage with WORM (Write Once Read Many) capability
