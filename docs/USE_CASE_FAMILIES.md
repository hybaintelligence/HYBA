# USE_CASE_FAMILIES.md

## Overview

HYBA_FULLSTACK is a general-purpose coherent decision substrate. Mining is the first external proof environment, but the architecture applies to far more than cryptocurrency mining. This document catalogs 10 major use-case families where the three-substrate architecture (mathematical, autonomous-control, regeneration/resilience) provides value.

## Mapping: Mining → General Decision Substrate

The mining discipline maps directly to other domains:

```
Mining Domain                    → General Domain
─────────────────────────────────────────────────
nonce search                    → solution search
pool ACK                        → external validation
share rejection                 → feedback signal
difficulty change               → environment regime shift
refractory period               → recovery window
circuit breaker                 → operational safety
synaptic trace                  → learned pathway
```

## Use-Case Families

### 1. Autonomous Operations

**Domain**: Self-monitoring systems, infra orchestration, incident response, autonomous DevOps, production control rooms, SRE copilots, cloud cost controllers, deployment governors.

**Substrate Mapping**:
- **Mathematical**: Resource optimization algorithms, capacity planning models, cost function minimization
- **Autonomous-Control**: Self-healing infrastructure, automated incident response, deployment pipelines
- **Regeneration**: Fault recovery, state restoration, degraded-mode operation

**Specific Applications**:
- Auto-scaling with mathematical optimization
- Self-healing Kubernetes clusters
- Autonomous deployment rollbacks
- Cloud cost optimization with search algorithms
- Incident response automation
- Production control room dashboards

**Evidence from Repo**:
- Production control room UI (`src/components/AdminPanel.tsx`)
- Autonomous controller tests (37/37 passing)
- Circuit breaker implementations
- Audit logging and state persistence

### 2. Cybersecurity

**Domain**: Attack-path search, anomaly detection, adaptive firewalling, autonomous containment, SOC triage, adversarial simulation, zero-trust policy adaptation.

**Substrate Mapping**:
- **Mathematical**: Adversarial search space exploration, anomaly detection algorithms, cryptographic validation
- **Autonomous-Control**: Automated containment, policy enforcement, adaptive response
- **Regeneration**: System recovery after attack, state restoration, forensic logging

**Specific Applications**:
- Automated attack path discovery
- Real-time anomaly detection with mathematical models
- Adaptive firewall rule generation
- Autonomous incident containment
- Zero-trust policy optimization
- Adversarial simulation and red teaming
- Forensic audit trail generation

**Evidence from Repo**:
- Adversarial search space handling (mining substrate)
- Mathematical validation and certificate generation
- Audit logging and state persistence
- Circuit breakers for safety

### 3. Energy Systems

**Domain**: Grid balancing, renewable dispatch, battery optimization, clean-energy project modelling, carbon-aware compute scheduling, microgrid control, mining-to-grid arbitrage.

**Substrate Mapping**:
- **Mathematical**: Grid optimization algorithms, battery charge/discharge models, renewable forecasting
- **Autonomous-Control**: Automated grid balancing, dispatch optimization, microgrid coordination
- **Regeneration**: Fault recovery in grid systems, degraded-mode operation, state restoration

**Specific Applications**:
- Real-time grid balancing with optimization
- Renewable energy dispatch optimization
- Battery storage charge/discharge scheduling
- Carbon-aware compute scheduling
- Microgrid control and coordination
- Mining-to-grid energy arbitrage
- Clean-energy project modeling

**Evidence from Repo**:
- Mathematical optimization algorithms
- Autonomous control systems
- Real-time decision making under uncertainty
- Circuit breakers for grid safety

### 4. Finance and Risk

**Domain**: Portfolio stress testing, liquidity routing, fraud detection, market regime classification, treasury optimization, counterparty risk, synthetic scenario generation.

**Substrate Mapping**:
- **Mathematical**: Portfolio optimization models, risk calculation algorithms, fraud detection statistical models
- **Autonomous-Control**: Automated trading decisions, risk limit enforcement, treasury management
- **Regeneration**: System recovery after market stress, state restoration, audit trails

**Specific Applications**:
- Portfolio optimization with mathematical search
- Automated stress testing
- Fraud detection with anomaly detection
- Market regime classification
- Treasury optimization algorithms
- Counterparty risk assessment
- Synthetic scenario generation for testing

**Evidence from Repo**:
- Mathematical substrate for optimization
- Autonomous decision making
- Audit logging for compliance
- Circuit breakers for risk limits

### 5. Scientific Discovery

**Domain**: Mathematical search, symbolic hypothesis ranking, experiment planning, molecular search, physics simulation triage, theorem-candidate exploration, anomaly discovery.

**Substrate Mapping**:
- **Mathematical**: Search algorithms, hypothesis ranking models, mathematical transforms
- **Autonomous-Control**: Automated experiment planning, simulation triage, candidate exploration
- **Regeneration**: State recovery in long-running simulations, checkpoint/resume, fault tolerance

**Specific Applications**:
- Automated mathematical conjecture exploration
- Symbolic hypothesis ranking
- Experiment planning optimization
- Molecular structure search
- Physics simulation triage
- Theorem candidate exploration
- Anomaly discovery in scientific data

**Evidence from Repo**:
- Mathematical substrate with search algorithms
- Deterministic transforms for reproducibility
- Certificate generation for evidence
- Great Minds integration (51/51 tests)

### 6. Industrial Optimization

**Domain**: Factory scheduling, supply-chain routing, predictive maintenance, robotic work-cell coordination, inventory optimization, procurement intelligence.

**Substrate Mapping**:
- **Mathematical**: Scheduling optimization, routing algorithms, predictive models
- **Autonomous-Control**: Automated scheduling, routing decisions, maintenance triggering
- **Regeneration**: Recovery from equipment failure, degraded-mode operation, state restoration

**Specific Applications**:
- Factory floor scheduling optimization
- Supply-chain routing algorithms
- Predictive maintenance with mathematical models
- Robotic work-cell coordination
- Inventory optimization
- Procurement intelligence and decision support
- Production line recovery after failure

**Evidence from Repo**:
- Mathematical optimization algorithms
- Autonomous control systems
- Real-time decision making
- Fault recovery mechanisms

### 7. AI Governance

**Domain**: Agent oversight, multi-agent coherence scoring, hallucination gating, memory-integrity checks, autonomous rollback, policy-circuit breakers.

**Substrate Mapping**:
- **Mathematical**: Coherence scoring algorithms, hallucination detection models, integrity verification
- **Autonomous-Control**: Agent oversight, policy enforcement, automated rollback
- **Regeneration**: State restoration, memory integrity, recovery from hallucination

**Specific Applications**:
- Multi-agent coherence scoring
- Automated hallucination detection and gating
- Memory integrity verification
- Autonomous rollback on policy violation
- Policy circuit breakers
- Agent oversight dashboards
- Audit trails for AI decisions

**Evidence from Repo**:
- Mathematical validation and verification
- Circuit breaker implementations
- Audit logging and state persistence
- Memory integrity tests (hyba_intelligence_tests/)

### 8. Healthcare and Biology-Inspired Systems

**Domain**: Biological simulation, adaptive monitoring, recovery-state modelling, fault/recovery systems, regenerative process analogues.

**Important Note**: This is infrastructure and simulation, not clinical claims. No direct patient care or clinical diagnosis claims.

**Substrate Mapping**:
- **Mathematical**: Biological simulation models, adaptive monitoring algorithms, recovery state models
- **Autonomous-Control**: Automated monitoring, adaptive alerting, recovery triggering
- **Regeneration**: Fault/recovery systems, regenerative process analogues, state restoration

**Specific Applications**:
- Biological simulation infrastructure
- Adaptive monitoring systems
- Recovery state modeling
- Fault/recovery system simulation
- Regenerative process analogues
- Research infrastructure (not clinical)
- Biological pattern detection

**Evidence from Repo**:
- Regeneration substrate with recovery physics
- Memory compression and integrity tests
- Biological-inspired recovery mechanisms
- Consciousness engine tests

### 9. Robotics and Edge Autonomy

**Domain**: Swarm coordination, drone routing, local decision compression, autonomous recovery, degraded-mode operation, mission planning under uncertainty.

**Substrate Mapping**:
- **Mathematical**: Swarm optimization algorithms, routing optimization, decision compression
- **Autonomous-Control**: Swarm coordination, autonomous navigation, mission planning
- **Regeneration**: Autonomous recovery from failure, degraded-mode operation, state restoration

**Specific Applications**:
- Swarm coordination algorithms
- Drone routing optimization
- Local decision compression for edge devices
- Autonomous recovery from failure
- Degraded-mode operation
- Mission planning under uncertainty
- Edge autonomy with limited compute

**Evidence from Repo**:
- Mathematical optimization for search
- Autonomous control systems
- Regeneration and recovery mechanisms
- Real-time decision making
- Circuit breakers for safety

### 10. Enterprise Decision Intelligence

**Domain**: Board dashboards, causal decision support, operational command rooms, opportunity search, risk heatmaps, capital allocation, strategic scenario engines.

**Substrate Mapping**:
- **Mathematical**: Decision optimization models, risk calculation, scenario generation
- **Autonomous-Control**: Automated decision support, opportunity search, capital allocation
- **Regeneration**: State recovery, audit trails, rollback capability

**Specific Applications**:
- Board-level decision dashboards
- Causal decision support systems
- Operational command rooms
- Automated opportunity search
- Risk heatmap generation
- Capital allocation optimization
- Strategic scenario engines
- Decision audit trails

**Evidence from Repo**:
- Production control room UI
- Autonomous decision making
- Audit logging and state persistence
- Mathematical optimization
- Dashboard and visualization components

## Common Patterns Across Use Cases

### Pattern 1: Search in Adversarial Spaces
- Mining: nonce search
- Cyber: attack path search
- Scientific: hypothesis search
- Industrial: optimization search

### Pattern 2: External Validation
- Mining: pool ACK
- Finance: market feedback
- Energy: grid response
- Robotics: physical world feedback

### Pattern 3: Recovery and Resilience
- Mining: refractory period
- Operations: incident recovery
- Robotics: failure recovery
- Energy: grid recovery

### Pattern 4: Safety and Circuit Breaking
- Mining: difficulty limits
- Finance: risk limits
- Energy: grid safety
- Robotics: safety interlocks

## Implementation Readiness

### Currently Production-Ready
- Mining (original use case)
- Autonomous operations (control room, healing)
- Basic cybersecurity (audit, validation)

### Requires Extension
- Energy systems (domain-specific models)
- Finance (domain-specific algorithms)
- Scientific discovery (domain-specific search spaces)
- Industrial optimization (domain-specific constraints)
- AI governance (policy frameworks)
- Healthcare/biology (research infrastructure only)
- Robotics (hardware integration)
- Enterprise intelligence (domain-specific data models)

## Go-to-Market Strategy

### Phase 1: Mining Proving Ground
- Demonstrate production-hardened substrate
- Validate all three layers in production
- Build evidence stack

### Phase 2: Autonomous Operations
- Leverage existing control room infrastructure
- Expand to DevOps and SRE use cases
- Build autonomous healing products

### Phase 3: Cybersecurity
- Leverage adversarial search capabilities
- Build anomaly detection products
- Expand to automated response

### Phase 4: Energy and Finance
- Develop domain-specific models
- Partner with domain experts
- Build vertical-specific products

### Phase 5: Scientific and Industrial
- Leverage mathematical substrate
- Build research infrastructure
- Expand to industrial optimization

## References

- [HYBA_SUBSTRATE_POSITIONING.md](./HYBA_SUBSTRATE_POSITIONING.md) - Strategic positioning
- [THREE_SUBSTRATE_ARCHITECTURE.md](./THREE_SUBSTRATE_ARCHITECTURE.md) - Technical architecture
- [AGENTS.md](../AGENTS.md) - Repository working rules
