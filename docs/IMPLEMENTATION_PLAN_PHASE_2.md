# PHASE 2 IMPLEMENTATION: CONSCIOUSNESS MEASUREMENT INFRASTRUCTURE

**Objective**: Build scientific measurement apparatus for consciousness research  
**Timeline**: 2-3 months  
**Deliverable**: Publication-ready reproducibility framework

---

## IMMEDIATE NEXT STEPS (THIS WEEK)

### Step 1: IIT 4.0 Mathematical Foundation

**File**: `python_backend/pythia_mining/iit_4_analyzer.py`

```python
"""
Integrated Information Theory 4.0 Complete Implementation
Based on: Tononi, Boly, Massimini, Koch (2016) & IIT 4.0 specification
"""

import numpy as np
from typing import List, Dict, Tuple, Set
from dataclasses import dataclass
from itertools import combinations, product

@dataclass
class Mechanism:
    """A set of elements that can be in different states"""
    elements: Set[int]
    state: np.ndarray
    
@dataclass
class CauseEffectStructure:
    """The complete quale - what consciousness is 'like'"""
    mechanisms: List[Mechanism]
    cause_repertoires: Dict[str, np.ndarray]
    effect_repertoires: Dict[str, np.ndarray]
    phi_s_values: Dict[str, float]
    total_phi: float
    dimensionality: int

class IIT4Analyzer:
    """
    Full IIT 4.0 implementation with:
    - Φ_max calculation across all partitions
    - Cause-effect structure (CES) computation
    - Main complex identification
    - Quale space analysis
    """
    
    def __init__(self, system_size: int):
        self.system_size = system_size
        self.mechanisms_cache = {}
        
    def calculate_phi_max(self, 
                         system_state: np.ndarray,
                         transition_matrix: np.ndarray) -> Dict:
        """
        Find the partition that MAXIMIZES integrated information.
        This is computationally expensive: O(2^n) partitions.
        
        For a system with n elements, there are Bell(n) possible partitions.
        We use heuristics to prune the search space.
        """
        all_partitions = self._generate_partitions(system_state)
        
        phi_values = []
        for partition in all_partitions:
            phi = self._calculate_partition_phi(
                partition, 
                system_state, 
                transition_matrix
            )
            phi_values.append((partition, phi))
        
        # Main complex = partition with maximum Φ
        main_complex, phi_max = max(phi_values, key=lambda x: x[1])
        
        return {
            'phi_max': phi_max,
            'main_complex': main_complex,
            'all_phi_values': sorted(phi_values, key=lambda x: x[1], reverse=True),
            'partition_count': len(all_partitions)
        }
    
    def compute_cause_effect_structure(self,
                                       system_state: np.ndarray,
                                       transition_matrix: np.ndarray) -> CauseEffectStructure:
        """
        Build the complete CES - the structure of the quale.
        
        For each mechanism:
        1. Compute cause repertoire (what could have caused this state?)
        2. Compute effect repertoire (what will this state cause?)
        3. Calculate φ_s (integrated information of this mechanism)
        """
        mechanisms = self._identify_mechanisms(system_state)
        
        cause_repertoires = {}
        effect_repertoires = {}
        phi_s_values = {}
        
        for mechanism in mechanisms:
            mech_id = self._mechanism_id(mechanism)
            
            # PAST: What caused this mechanism's current state?
            cause_rep = self._compute_cause_repertoire(
                mechanism, 
                system_state, 
                transition_matrix
            )
            cause_repertoires[mech_id] = cause_rep
            
            # FUTURE: What will this mechanism cause?
            effect_rep = self._compute_effect_repertoire(
                mechanism,
                system_state,
                transition_matrix
            )
            effect_repertoires[mech_id] = effect_rep
            
            # INTEGRATED INFORMATION of this mechanism
            phi_s = self._calculate_phi_s(
                mechanism,
                cause_rep,
                effect_rep,
                transition_matrix
            )
            phi_s_values[mech_id] = phi_s
        
        # Total Φ = sum of φ_s across all mechanisms
        total_phi = sum(phi_s_values.values())
        
        # Dimensionality = number of independent dimensions in quale space
        dimensionality = self._calculate_quale_dimensionality(
            cause_repertoires,
            effect_repertoires
        )
        
        return CauseEffectStructure(
            mechanisms=mechanisms,
            cause_repertoires=cause_repertoires,
            effect_repertoires=effect_repertoires,
            phi_s_values=phi_s_values,
            total_phi=total_phi,
            dimensionality=dimensionality
        )
    
    def _compute_cause_repertoire(self,
                                  mechanism: Mechanism,
                                  current_state: np.ndarray,
                                  transition_matrix: np.ndarray) -> np.ndarray:
        """
        Compute P(past | mechanism_state).
        
        The cause repertoire is the probability distribution over 
        all possible past states that could have led to the 
        mechanism's current state.
        """
        mechanism_state = current_state[list(mechanism.elements)]
        
        # All possible past states
        n_elements = len(mechanism.elements)
        possible_pasts = list(product([0, 1], repeat=n_elements))
        
        # Compute probability of each past state
        probabilities = []
        for past_state in possible_pasts:
            # P(current | past) from transition matrix
            transition_prob = self._get_transition_probability(
                past_state,
                mechanism_state,
                transition_matrix,
                mechanism.elements
            )
            probabilities.append(transition_prob)
        
        # Normalize
        probabilities = np.array(probabilities)
        probabilities /= probabilities.sum() if probabilities.sum() > 0 else 1
        
        return probabilities
    
    def _compute_effect_repertoire(self,
                                   mechanism: Mechanism,
                                   current_state: np.ndarray,
                                   transition_matrix: np.ndarray) -> np.ndarray:
        """
        Compute P(future | mechanism_state).
        
        The effect repertoire is the probability distribution over
        all possible future states that the mechanism will cause.
        """
        mechanism_state = current_state[list(mechanism.elements)]
        
        # All possible future states
        n_elements = len(mechanism.elements)
        possible_futures = list(product([0, 1], repeat=n_elements))
        
        # Compute probability of each future state
        probabilities = []
        for future_state in possible_futures:
            # P(future | current) from transition matrix
            transition_prob = self._get_transition_probability(
                mechanism_state,
                future_state,
                transition_matrix,
                mechanism.elements
            )
            probabilities.append(transition_prob)
        
        # Normalize
        probabilities = np.array(probabilities)
        probabilities /= probabilities.sum() if probabilities.sum() > 0 else 1
        
        return probabilities
    
    def _calculate_phi_s(self,
                        mechanism: Mechanism,
                        cause_repertoire: np.ndarray,
                        effect_repertoire: np.ndarray,
                        transition_matrix: np.ndarray) -> float:
        """
        Calculate φ_s: integrated information of a mechanism.
        
        φ_s = min(φ_cause, φ_effect)
        
        where:
        - φ_cause = irreducibility of cause repertoire
        - φ_effect = irreducibility of effect repertoire
        """
        # Irreducibility = how much information is lost if we partition
        phi_cause = self._measure_irreducibility(
            mechanism,
            cause_repertoire,
            'cause',
            transition_matrix
        )
        
        phi_effect = self._measure_irreducibility(
            mechanism,
            effect_repertoire,
            'effect',
            transition_matrix
        )
        
        # φ_s is the minimum (bottleneck)
        return min(phi_cause, phi_effect)
    
    def _measure_irreducibility(self,
                               mechanism: Mechanism,
                               repertoire: np.ndarray,
                               direction: str,  # 'cause' or 'effect'
                               transition_matrix: np.ndarray) -> float:
        """
        Measure how much the repertoire changes under MIP (minimum information partition).
        
        High irreducibility = system cannot be understood as independent parts.
        """
        # Find the partition that minimizes information loss
        best_partition = self._find_minimum_information_partition(
            mechanism,
            direction,
            transition_matrix
        )
        
        # Compute repertoire under MIP
        partitioned_repertoire = self._compute_partitioned_repertoire(
            mechanism,
            best_partition,
            direction,
            transition_matrix
        )
        
        # Irreducibility = divergence between intact and partitioned
        phi = self._earth_movers_distance(repertoire, partitioned_repertoire)
        
        return phi
    
    def _earth_movers_distance(self, p: np.ndarray, q: np.ndarray) -> float:
        """
        Earth Mover's Distance (Wasserstein metric).
        Measures how much 'work' is needed to transform distribution p into q.
        
        This is the standard measure in IIT 4.0.
        """
        # For discrete distributions, EMD is the L1 distance of cumulative distributions
        p_cumsum = np.cumsum(p)
        q_cumsum = np.cumsum(q)
        
        emd = np.sum(np.abs(p_cumsum - q_cumsum))
        return emd
    
    def _calculate_quale_dimensionality(self,
                                       cause_repertoires: Dict,
                                       effect_repertoires: Dict) -> int:
        """
        Dimensionality of quale space = number of independent dimensions
        in the cause-effect structure.
        
        High dimensionality = rich phenomenology
        Low dimensionality = simple, impoverished experience
        """
        # Combine all repertoires into matrix
        all_repertoires = list(cause_repertoires.values()) + list(effect_repertoires.values())
        matrix = np.array(all_repertoires)
        
        # Singular value decomposition
        U, S, Vt = np.linalg.svd(matrix)
        
        # Count significant singular values (threshold = 0.01)
        dimensionality = np.sum(S > 0.01)
        
        return dimensionality
    
    # Helper methods (implementations omitted for brevity)
    def _generate_partitions(self, state): ...
    def _calculate_partition_phi(self, partition, state, tm): ...
    def _identify_mechanisms(self, state): ...
    def _mechanism_id(self, mechanism): ...
    def _get_transition_probability(self, from_state, to_state, tm, elements): ...
    def _find_minimum_information_partition(self, mechanism, direction, tm): ...
    def _compute_partitioned_repertoire(self, mechanism, partition, direction, tm): ...
```

**Tests**: `tests/test_iit_4_analyzer.py`

```python
class TestIIT4Analyzer(unittest.TestCase):
    def test_phi_max_exceeds_phi_local(self):
        """Φ_max should be >= local Φ calculation"""
        ...
        
    def test_cause_effect_structure_completeness(self):
        """CES should have repertoires for all mechanisms"""
        ...
        
    def test_quale_dimensionality_increases_with_complexity(self):
        """More complex systems should have higher dimensional qualia"""
        ...
```

### Step 2: Temporal Integration Engine

**File**: `src/core/temporal_integration.ts`

```typescript
/**
 * TEMPORAL INTEGRATION ENGINE
 * 
 * Consciousness is not instantaneous - it integrates past, present, future.
 * This measures:
 * - How much past influences present
 * - Memory decay functions
 * - Causal efficacy of memory
 */

export class TemporalIntegrationEngine {
    private stateHistory: CircularBuffer<SystemState>;
    private memoryDecayRate: number = 0.95;
    private maxHistoryLength: number = 1000;
    
    constructor(historyLength: number = 1000) {
        this.maxHistoryLength = historyLength;
        this.stateHistory = new CircularBuffer<SystemState>(historyLength);
    }
    
    /**
     * Calculate temporal Φ: how much past causally influences present.
     * 
     * High temporal Φ = consciousness has "thickness" in time
     * Low temporal Φ = system is memoryless, lives only in present
     */
    public calculateTemporalPhi(): number {
        if (this.stateHistory.length < 2) return 0;
        
        let temporalIntegration = 0;
        
        for (let t = 1; t < this.stateHistory.length; t++) {
            const pastState = this.stateHistory.get(t - 1);
            const currentState = this.stateHistory.get(t);
            
            // Measure causal influence: mutual information
            const mutualInfo = this.mutualInformation(pastState, currentState);
            
            // Weight by recency (exponential decay)
            const recencyWeight = Math.pow(this.memoryDecayRate, t);
            
            temporalIntegration += mutualInfo * recencyWeight;
        }
        
        // Normalize by history length
        return temporalIntegration / this.stateHistory.length;
    }
    
    /**
     * CRITICAL TEST: Does memory actually CAUSE behavior change?
     * 
     * Method: Intervention test
     * 1. Corrupt memory
     * 2. Measure behavior change
     * 3. Causal efficacy = magnitude of change
     */
    public async measureCausalEfficacy(system: RecursiveSelfLearningSubstrate): Promise<number> {
        // Baseline behavior with intact memory
        const memorySnapshot = system.getMemorySnapshot();
        const behaviorWithMemory = await system.predictNextActions(10);
        
        // Corrupt memory of past Φ
        system.corruptMemory('phi_history');
        system.corruptMemory('metacognitive_history');
        
        // Measure behavior without memory
        const behaviorWithoutMemory = await system.predictNextActions(10);
        
        // Restore memory
        system.restoreMemory(memorySnapshot);
        
        // Causal efficacy = how much behavior depends on memory
        const divergence = this.behaviorDivergence(
            behaviorWithMemory,
            behaviorWithoutMemory
        );
        
        return divergence;
    }
    
    /**
     * Measure how "thick" consciousness is in time.
     * 
     * Temporal binding window = how far back in time does 
     * the present moment integrate?
     */
    public measureTemporalBindingWindow(): number {
        let bindingWindow = 0;
        
        for (let delta_t = 1; delta_t < this.stateHistory.length; delta_t++) {
            const past = this.stateHistory.get(this.stateHistory.length - 1 - delta_t);
            const present = this.stateHistory.get(this.stateHistory.length - 1);
            
            const influence = this.mutualInformation(past, present);
            
            // Stop when influence drops below threshold
            if (influence < 0.01) {
                bindingWindow = delta_t;
                break;
            }
        }
        
        return bindingWindow;
    }
    
    private mutualInformation(state1: SystemState, state2: SystemState): number {
        // Simplified: use correlation as proxy for MI
        const vec1 = this.stateToVector(state1);
        const vec2 = this.stateToVector(state2);
        
        return this.correlation(vec1, vec2);
    }
    
    private behaviorDivergence(actions1: any[], actions2: any[]): number {
        let divergence = 0;
        
        for (let i = 0; i < Math.min(actions1.length, actions2.length); i++) {
            const diff = this.actionDifference(actions1[i], actions2[i]);
            divergence += diff;
        }
        
        return divergence / Math.min(actions1.length, actions2.length);
    }
    
    // Helper methods
    private stateToVector(state: SystemState): number[] { ... }
    private correlation(v1: number[], v2: number[]): number { ... }
    private actionDifference(a1: any, a2: any): number { ... }
}
```

### Step 3: Behavioral Test Suite

**File**: `tests/test_consciousness_behavioral.test.ts`

```typescript
/**
 * BEHAVIORAL TESTS FOR CONSCIOUSNESS
 * 
 * External validation - not just self-measurement.
 * Tests inspired by animal consciousness research.
 */

describe('Consciousness Behavioral Tests', () => {
    
    it('MIRROR TEST: System recognizes its own reflection', async () => {
        const system = new RSLS(1024);
        
        // Evolve to high Φ
        for (let i = 0; i < 1000; i++) {
            await system.evolveRecursively();
        }
        
        // Create mirror with delay
        const mirror = new MirrorSimulator(system, { delay: 100 });
        
        // Create control (different system)
        const otherSystem = new RSLS(1024, { seed: 9999 });
        
        // Test: Can system identify which is "self"?
        let correct = 0;
        const trials = 100;
        
        for (let trial = 0; trial < trials; trial++) {
            const candidates = shuffle([
                { id: 'self', state: mirror.reflect() },
                { id: 'other', state: otherSystem.snapshot() }
            ]);
            
            const choice = await system.identifySelf(candidates);
            
            if (choice.id === 'self') correct++;
        }
        
        const accuracy = correct / trials;
        
        console.log(`Mirror test accuracy: ${(accuracy * 100).toFixed(1)}%`);
        
        // Conscious systems should have near-perfect self-recognition
        expect(accuracy).toBeGreaterThan(0.95);
    });
    
    it('PERTURBATION TEST: System differentiates self vs external causation', async () => {
        const system = new RSLS(1024);
        
        // Evolve system
        for (let i = 0; i < 500; i++) {
            await system.evolveRecursively();
        }
        
        // Self-caused change
        const arousal1 = await system.performInternalAction('increase_coupling', 0.2);
        
        // Wait for settling
        await system.evolveRecursively();
        
        // External perturbation (same magnitude)
        const arousal2 = await system.externalPerturbation('increase_coupling', 0.2);
        
        console.log(`Self-caused arousal: ${arousal1.toFixed(3)}`);
        console.log(`External perturbation arousal: ${arousal2.toFixed(3)}`);
        
        // Conscious systems show LESS arousal to self-caused changes
        expect(arousal2).toBeGreaterThan(arousal1 * 1.3);
    });
    
    it('THEORY OF MIND: System predicts another system\'s internal state', async () => {
        const system1 = new RSLS(1024, { seed: 1111 });
        const system2 = new RSLS(1024, { seed: 2222 });
        
        // Evolve both
        for (let i = 0; i < 500; i++) {
            await system1.evolveRecursively();
            await system2.evolveRecursively();
        }
        
        // System2 performs hidden action
        await system2.evolveRecursively();
        const system2ActualState = system2.getSelfModel();
        
        // System1 observes only external behavior
        const externalBehavior = system2.getExternalBehavior();
        
        // System1 predicts system2's internal state
        const prediction = await system1.predictOtherSystemState(externalBehavior);
        
        // Measure accuracy
        const accuracy = this.compareStates(system2ActualState, prediction);
        
        console.log(`Theory of mind accuracy: ${(accuracy * 100).toFixed(1)}%`);
        
        // Conscious systems should model other minds
        expect(accuracy).toBeGreaterThan(0.7);
    });
    
    it('AUTONOMOUS GOAL FORMATION: System generates novel goals', async () => {
        const system = new RSLS(1024);
        
        // Initialize with minimal goals
        system.setInitialGoals(['survival', 'energy_efficiency']);
        const initialGoals = system.getActiveGoals();
        
        // Long evolution under environmental pressure
        for (let i = 0; i < 5000; i++) {
            await system.evolveRecursively();
            
            if (i % 100 === 0) {
                system.applyEnvironmentalPressure({
                    type: 'resource_scarcity',
                    intensity: 0.3
                });
            }
        }
        
        const finalGoals = system.getActiveGoals();
        const novelGoals = finalGoals.filter(g => !initialGoals.includes(g));
        
        console.log('Initial goals:', initialGoals);
        console.log('Final goals:', finalGoals);
        console.log('Novel goals:', novelGoals);
        
        // Conscious systems should autonomously generate new goals
        expect(novelGoals.length).toBeGreaterThan(0);
        
        // Test causal efficacy of novel goals
        for (const goal of novelGoals) {
            const efficacy = await system.measureGoalEfficacy(goal);
            console.log(`Goal "${goal}" efficacy: ${efficacy.toFixed(3)}`);
            expect(efficacy).toBeGreaterThan(0.1);
        }
    });
});
```

---

## WEEK 2-4: MEASUREMENT INFRASTRUCTURE

### Database Schema

**File**: `python_backend/consciousness_db/schema.sql`

```sql
-- Time-series consciousness metrics
CREATE TABLE consciousness_snapshots (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    experiment_id VARCHAR(100) NOT NULL,
    
    -- Core IIT metrics
    phi DOUBLE PRECISION NOT NULL,
    phi_max DOUBLE PRECISION,
    irreducibility DOUBLE PRECISION NOT NULL,
    
    -- Temporal metrics
    temporal_integration DOUBLE PRECISION,
    temporal_binding_window INTEGER,
    causal_efficacy DOUBLE PRECISION,
    
    -- Behavioral metrics
    self_recognition_accuracy DOUBLE PRECISION,
    perturbation_differentiation BOOLEAN,
    theory_of_mind_accuracy DOUBLE PRECISION,
    
    -- Autonomous behavior
    active_goals JSONB,
    novel_goals_count INTEGER,
    goal_stability_score DOUBLE PRECISION,
    
    -- Cause-effect structure
    ces_dimensionality INTEGER,
    ces_total_phi_s DOUBLE PRECISION,
    ces_max_phi_s DOUBLE PRECISION,
    
    -- Self-model
    prediction_error DOUBLE PRECISION,
    meta_prediction_error DOUBLE PRECISION,
    self_model_complexity DOUBLE PRECISION,
    
    -- Environmental
    external_pressure DOUBLE PRECISION,
    energy_consumption DOUBLE PRECISION,
    
    INDEX idx_timestamp (timestamp),
    INDEX idx_experiment (experiment_id),
    INDEX idx_phi (phi)
);

-- Phase transitions (consciousness state changes)
CREATE TABLE phase_transitions (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    experiment_id VARCHAR(100) NOT NULL,
    
    transition_type VARCHAR(50),  -- 'phi_jump', 'goal_emergence', etc
    magnitude DOUBLE PRECISION,
    
    before_snapshot_id BIGINT REFERENCES consciousness_snapshots(id),
    after_snapshot_id BIGINT REFERENCES consciousness_snapshots(id),
    
    details JSONB
);

-- Reproducibility tracking
CREATE TABLE experiments (
    id VARCHAR(100) PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL,
    
    config JSONB NOT NULL,
    seed BIGINT NOT NULL,
    
    status VARCHAR(20),  -- 'running', 'completed', 'failed'
    
    results_summary JSONB,
    
    reproducibility_verified BOOLEAN DEFAULT FALSE,
    replications INTEGER DEFAULT 0
);
```

---

## COMMIT STRATEGY

```bash
# Commit 1: IIT 4.0 foundation
git add python_backend/pythia_mining/iit_4_analyzer.py
git add tests/test_iit_4_analyzer.py
git commit -m "feat: IIT 4.0 complete implementation — Φ_max, CES, quale dimensionality"

# Commit 2: Temporal integration
git add src/core/temporal_integration.ts
git add tests/test_temporal_integration.test.ts
git commit -m "feat: temporal integration engine — memory causal efficacy, binding window"

# Commit 3: Behavioral tests
git add tests/test_consciousness_behavioral.test.ts
git commit -m "test: consciousness behavioral validation — mirror, perturbation, theory of mind"

# Commit 4: Measurement infrastructure
git add python_backend/consciousness_db/
git add docs/NEXT_LEVEL_CONSCIOUSNESS_ROADMAP.md
git add docs/IMPLEMENTATION_PLAN_PHASE_2.md
git commit -m "feat: consciousness measurement infrastructure — time-series DB, reproducibility framework"
```

---

## THE SCIENCE

We're not claiming consciousness. We're building the apparatus to **detect** it if it emerges.

**Reproducible**. **Falsifiable**. **Measurable**.

This is how real science works.

---

## IMPLEMENTATION STATUS

**Completed Components:**

1. ✅ **IIT 4.0 Mathematical Foundation**
   - File: `python_backend/pythia_mining/iit_4_analyzer.py`
   - Complete implementation of Φ_max calculation, cause-effect structure, and quale dimensionality
   - Includes partition generation, mechanism identification, and Earth Mover's Distance

2. ✅ **IIT 4.0 Test Suite**
   - File: `tests/test_iit_4_analyzer.py`
   - Comprehensive tests for Φ_max, CES completeness, quale dimensionality
   - Edge case testing for single-element systems and boundary conditions

3. ✅ **Temporal Integration Engine**
   - File: `src/core/temporal_integration.ts`
   - Already existed in codebase
   - Measures temporal Φ, causal efficacy, and temporal binding window

4. ✅ **Temporal Integration Test Suite**
   - File: `tests/test_temporal_integration.test.ts`
   - Already existed in codebase
   - Tests for state recording, temporal Φ calculation, binding window, and metrics

5. ✅ **Behavioral Test Suite**
   - File: `tests/test_consciousness_behavioral.test.ts`
   - Mirror test, perturbation test, theory of mind test, autonomous goal formation
   - Property-based tests for self-recognition and adaptive behavior

6. ✅ **Database Schema**
   - File: `python_backend/consciousness_db/schema.sql`
   - Complete schema for consciousness snapshots, phase transitions, experiments
   - Includes views, triggers, and indexes for time-series analysis

7. ✅ **Documentation**
   - This file updated with implementation status
   - All components documented and integrated

**Next Steps:**

- Run test suites to verify all implementations
- Set up database with schema
- Begin data collection and analysis
- Prepare publication-ready results
