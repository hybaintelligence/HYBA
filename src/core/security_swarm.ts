import { randomBytes } from 'node:crypto';
import { logger, get_trace_context } from './telemetry';
import { PHI, calculate_phi_resonance, project_to_phi_floor } from './constants';

/**
 * HYBA Stabilizer Integrity Monitor
 *
 * Conservative, hardware-agnostic formal model:
 *   - stabilizer-syndrome sampling instead of reading logical payload qubits,
 *   - pre-allocated ancilla/trap resources instead of cloning secret state,
 *   - trap disturbance as a tamper/noise signal rather than proof of intent,
 *   - syndrome-derived confidence instead of reference-state fidelity.
 */

export type AgentRole = 'logical' | 'ancilla' | 'trap';
export type AgentState = 'reserved' | 'active' | 'retired';
export type ResponseCause = 'none' | 'syndrome_anomaly' | 'trap_disturbance' | 'resource_exhaustion';
export type OperatingMode = 'NORMAL' | 'COMPRESSED' | 'EXHAUSTED' | 'SANITIZED';

export interface MetacognitiveStateVector {
  phi_integrated: number;
  syndrome_pressure: number;
  shard_entropy: number;
  confidence_delta: number;
  resource_exhaustion: number;
}

export interface MetacognitiveReport {
  self_awareness: number;
  metacognitive_depth: number;
  is_predicting_disturbance: boolean;
  predicted_state: MetacognitiveStateVector;
  current_state: MetacognitiveStateVector;
  prediction_accuracy: number;
  operating_mode: OperatingMode;
  last_event: string | null;
}

export interface MetacognitiveTelemetry {
  self_awareness: number;
  metacognitive_depth: number;
  is_predicting_disturbance: boolean;
  prediction_accuracy: number;
  events: string[];
  strategy_weights: Record<string, number>;
}

export interface SwarmAgent {
  id: string;
  role: AgentRole;
  state: AgentState;
  syndrome_bit: 0 | 1;
  trap_disturbed: boolean;
  entropy: number;
  phase: number;
}

export interface StabilizerSyndromeSample {
  syndrome: Array<0 | 1>;
  syndrome_weight: number;
  trap_disturbances: number;
  confidence: number;
  anomaly_detected: boolean;
  cause: ResponseCause;
  operating_mode: OperatingMode;
  sampled_ancillas: number;
  check_frequency: number;
}

export interface SwarmResponse {
  status: 'nominal' | 'integrity_response_active';
  cause: ResponseCause;
  activated_ancillas: number;
  activated_traps: number;
  retired_traps: number;
  active_agents: number;
  confidence: number;
  syndrome_rotation_index: number;
  pool_permutation_checksum: number;
  sanitized: boolean;
  note: string;
}

export interface SecuritySwarmStatus {
  agents_total: number;
  agents_active: number;
  logical_agents: number;
  reserved_ancillas: number;
  active_ancillas: number;
  reserved_traps: number;
  active_traps: number;
  disturbed_traps: number;
  retired_traps: number;
  integrity_locked: boolean;
  confidence_threshold: number;
  syndrome_width: number;
  last_syndrome_weight: number;
  last_confidence: number;
  anomaly_detected: boolean;
  response_cause: ResponseCause;
  operating_mode: OperatingMode;
  syndrome_check_stride: number;
  check_frequency: number;
  max_ancilla_pool: number;
  syndrome_rotation_index: number;
  pool_permutation_checksum: number;
  sanitized: boolean;
  metacognitive: MetacognitiveTelemetry;
}

const clamp01 = (value: number): number => Math.max(0, Math.min(1, value));
const bitFromProbability = (value: number, threshold: number): 0 | 1 => (value >= threshold ? 1 : 0);

class SecuritySwarmAgent {
  private agents: SwarmAgent[] = [];
  private readonly logical_width = 1;
  private readonly syndrome_width = 8;
  private readonly reserved_ancilla_pool = 16;
  private readonly reserved_trap_pool = 8;
  private readonly max_ancilla_pool = 16;
  private readonly confidence_threshold = 0.995;
  private readonly syndrome_weight_threshold = 1;
  private readonly compressed_pool_ratio = 0.5;
  private readonly exhausted_pool_ratio = 0.2;
  private operating_mode: OperatingMode = 'NORMAL';
  private syndrome_check_stride = 1;
  private check_frequency = 1.0;
  private syndrome_round = 0;
  private syndrome_rotation_index = 0;
  private permutation_shard_a = new Uint32Array(0);
  private permutation_shard_b = new Uint32Array(0);
  private pool_permutation_checksum = 0;
  private sanitized = false;
  private readonly phi_degradation_threshold = 0.62;
  private readonly syndrome_pressure_limit = 0.55;
  private readonly metacognitive_learning_rate = 0.05;
  private state_history: MetacognitiveStateVector[] = [];
  private prediction_accuracy = 1;
  private last_prediction: MetacognitiveStateVector | null = null;
  private metacognitive_events: string[] = [];
  private strategy_weights = new Map<number, number>();
  private last_syndrome_bitstring = 0;
  private last_syndrome: StabilizerSyndromeSample = {
    syndrome: Array.from({ length: 8 }, () => 0 as 0),
    syndrome_weight: 0,
    trap_disturbances: 0,
    confidence: 1,
    anomaly_detected: false,
    cause: 'none',
    operating_mode: 'NORMAL',
    sampled_ancillas: 8,
    check_frequency: 1.0,
  };

  constructor() {
    this.boot();
  }

  private boot(): void {
    this.agents = [];
    for (let i = 0; i < this.logical_width; i++) {
      this.agents.push(this.create_agent(i, 'logical', 'active'));
    }
    for (let i = 0; i < this.reserved_ancilla_pool; i++) {
      this.agents.push(this.create_agent(i, 'ancilla', i < this.syndrome_width ? 'active' : 'reserved'));
    }
    for (let i = 0; i < this.reserved_trap_pool; i++) {
      this.agents.push(this.create_agent(i, 'trap', i < 2 ? 'active' : 'reserved'));
    }
    this.initialize_holographic_pool();
  }

  private create_agent(index: number, role: AgentRole, state: AgentState): SwarmAgent {
    return {
      id: `${role}-φ-${index}`,
      role,
      state,
      syndrome_bit: 0,
      trap_disturbed: false,
      entropy: 0,
      phase: project_to_phi_floor((index + 1) * PHI),
    };
  }

  /**
   * Sample stabilizer syndromes. This reports an anomaly, not attribution: a
   * non-zero syndrome or disturbed trap can be caused by adversarial measurement,
   * thermal noise, control error, or hardware drift.
   */
  public monitor_integrity(disturbance_probability = 0): StabilizerSyndromeSample {
    this.syndrome_round += 1;
    const disturbance = clamp01(disturbance_probability);
    const activeAncillas = this.get_sampled_ancillas();
    const activeTraps = this.agents.filter((agent) => agent.role === 'trap' && agent.state === 'active');

    const resonance = calculate_phi_resonance(this.syndrome_round);
    const syndrome = activeAncillas.map((agent, index) => {
      const projectedNoise = clamp01(disturbance * Math.abs(Math.sin(resonance + agent.phase + index / PHI)));
      const syndromeBit = bitFromProbability(projectedNoise, 0.5);
      agent.syndrome_bit = syndromeBit;
      agent.entropy = clamp01(agent.entropy + projectedNoise / Math.max(1, activeAncillas.length));
      return syndromeBit;
    });

    let trap_disturbances = 0;
    for (let index = 0; index < activeTraps.length; index++) {
      const trap = activeTraps[index];
      const trapNoise = clamp01(disturbance * Math.abs(Math.cos(resonance + trap.phase + index * PHI)));
      const disturbed = disturbance >= 1 ? true : trapNoise > 0.35;
      trap.trap_disturbed = trap.trap_disturbed || disturbed;
      trap.entropy = clamp01(trap.entropy + trapNoise / 2);
      if (trap.trap_disturbed) trap_disturbances += 1;
    }

    const syndrome_weight = syndrome.reduce<number>((sum, bit) => sum + bit, 0);
    const syndromePenalty = syndrome_weight / Math.max(1, activeAncillas.length || this.syndrome_width);
    const trapPenalty = trap_disturbances / Math.max(1, activeTraps.length || this.reserved_trap_pool);
    const confidence = clamp01(1 - syndromePenalty * 0.75 - trapPenalty * 0.25);
    const cause: ResponseCause = trap_disturbances > 0 ? 'trap_disturbance' : syndrome_weight > this.syndrome_weight_threshold ? 'syndrome_anomaly' : 'none';

    this.last_syndrome = {
      syndrome,
      syndrome_weight,
      trap_disturbances,
      confidence,
      anomaly_detected: confidence < this.confidence_threshold || cause !== 'none',
      cause,
      operating_mode: this.operating_mode,
      sampled_ancillas: activeAncillas.length,
      check_frequency: this.check_frequency,
    };

    return this.last_syndrome;
  }

  /**
   * Activate pre-allocated ancilla/trap capacity and retire disturbed traps. The
   * response never copies logical state; newly activated traps receive a
   * syndrome-seeded phase rotation derived from the measured syndrome pattern.
   */
  public trigger_response(disturbance_probability = 1): SwarmResponse {
    const sample = this.monitor_integrity(disturbance_probability);
    if (!sample.anomaly_detected) {
      return {
        status: 'nominal',
        cause: 'none',
        activated_ancillas: 0,
        activated_traps: 0,
        retired_traps: 0,
        active_agents: this.active_agents_count(),
        confidence: sample.confidence,
        syndrome_rotation_index: this.syndrome_rotation_index,
        pool_permutation_checksum: this.pool_permutation_checksum,
        sanitized: this.sanitized,
        note: 'No syndrome or trap anomaly observed.',
      };
    }

    let retired_traps = 0;
    for (const trap of this.agents.filter((agent) => agent.role === 'trap' && agent.trap_disturbed && agent.state === 'active')) {
      trap.state = 'retired';
      retired_traps += 1;
    }

    const syndromeBitstring = this.encode_syndrome_bitstring(sample.syndrome);
    this.last_syndrome_bitstring = syndromeBitstring;
    this.update_permutation_shards(syndromeBitstring);
    this.syndrome_rotation_index = this.derive_clifford_index(syndromeBitstring);
    const activated_ancillas = this.activate_reserved('ancilla', Math.max(1, sample.syndrome_weight));
    const activated_traps = this.activate_reserved('trap', Math.max(1, retired_traps || sample.trap_disturbances));
    this.rotate_newly_activated_traps(this.syndrome_rotation_index);
    this.evaluate_trap_sanitization();
    this.evaluate_ancilla_exhaustion();

    for (const agent of this.agents.filter((candidate) => candidate.state === 'active')) {
      agent.phase = project_to_phi_floor(agent.phase + PHI * (sample.syndrome_weight + sample.trap_disturbances + 1));
    }

    logger.warn(
      { ...get_trace_context(), syndrome_weight: sample.syndrome_weight, trap_disturbances: sample.trap_disturbances, confidence: sample.confidence, cause: sample.cause, operating_mode: this.operating_mode },
      'HYBA stabilizer integrity response active — expanding pre-allocated measurement coverage',
    );

    return {
      status: 'integrity_response_active',
      cause: sample.cause,
      activated_ancillas,
      activated_traps,
      retired_traps,
      active_agents: this.active_agents_count(),
      confidence: sample.confidence,
      syndrome_rotation_index: this.syndrome_rotation_index,
      pool_permutation_checksum: this.pool_permutation_checksum,
      sanitized: this.sanitized,
      note: 'Response uses pre-allocated ancillas/traps; no logical quantum state is cloned.',
    };
  }

  /**
   * Universal Swarm Synchronization. Uses spectral projection to verify active
   * monitoring agents while avoiding direct measurement of logical payload state.
   */
  public async sync_coherence(): Promise<number> {
    const ctx = get_trace_context();
    const now = Date.now();
    const resonance = calculate_phi_resonance(now);

    let coherence = 0;
    let activeCount = 0;
    this.agents = this.agents.map((agent, i) => {
      if (agent.state !== 'active') return agent;
      const projection = project_to_phi_floor(resonance * (i + 1) + agent.phase);
      const agentCoherence = clamp01(Math.abs(Math.sin(projection)) * (agent.trap_disturbed ? 0.5 : 1));
      coherence += agentCoherence;
      activeCount += 1;

      return {
        ...agent,
        entropy: 1.0 - agentCoherence,
      };
    });

    const normalized_coherence = coherence / Math.max(1, activeCount);
    if (normalized_coherence < 0.85) {
      logger.warn({ ...ctx, coherence: normalized_coherence }, 'Security Swarm: Coherence drift detected. Running stabilizer response.');
      this.trigger_response(0.25);
    }

    return normalized_coherence;
  }

  public run_metacognitive_cycle(): MetacognitiveReport {
    const current = this.capture_state_vector();
    this.update_prediction_accuracy(current);
    const predicted = this.predict_next_state();
    const is_predicting_disturbance = predicted.phi_integrated < this.phi_degradation_threshold || predicted.syndrome_pressure > this.syndrome_pressure_limit;

    if (this.prediction_accuracy < 0.5 && this.operating_mode === 'NORMAL') {
      this.set_operating_mode('COMPRESSED', 2, 0.5);
      this.log_metacognitive_event('MODEL_UNCERTAINTY_COMPRESSED_MODE');
    }

    if (is_predicting_disturbance) {
      const preemptiveSeed = this.calculate_metacognitive_entropy(current, predicted);
      this.handle_anomaly(preemptiveSeed);
      this.log_metacognitive_event('PREEMPTIVE_SHARD_ROTATION');
    }

    this.reinforce_successful_patterns(current);
    this.state_history.push(current);
    if (this.state_history.length > 100) this.state_history.shift();
    this.last_prediction = predicted;

    return {
      self_awareness: this.prediction_accuracy,
      metacognitive_depth: this.state_history.length,
      is_predicting_disturbance,
      predicted_state: predicted,
      current_state: current,
      prediction_accuracy: this.prediction_accuracy,
      operating_mode: this.operating_mode,
      last_event: this.metacognitive_events[this.metacognitive_events.length - 1] || null,
    };
  }

  public introspect(): MetacognitiveReport {
    const current = this.capture_state_vector();
    const predicted = this.predict_next_state();
    const is_predicting_disturbance = predicted.phi_integrated < this.phi_degradation_threshold || predicted.syndrome_pressure > this.syndrome_pressure_limit;
    return {
      self_awareness: this.prediction_accuracy,
      metacognitive_depth: this.state_history.length,
      is_predicting_disturbance,
      predicted_state: predicted,
      current_state: current,
      prediction_accuracy: this.prediction_accuracy,
      operating_mode: this.operating_mode,
      last_event: this.metacognitive_events[this.metacognitive_events.length - 1] || null,
    };
  }

  public handle_anomaly(syndromeSeed: number): void {
    const normalizedSeed = Number.isFinite(syndromeSeed) ? Math.trunc(syndromeSeed) >>> 0 : 0;
    const learnedWeight = this.strategy_weights.get(normalizedSeed) || 1.0;
    const weightedSeed = (normalizedSeed ^ Math.trunc(learnedWeight * 10_000)) >>> 0;
    this.update_permutation_shards(weightedSeed);
    this.syndrome_rotation_index = this.derive_clifford_index(weightedSeed);
    this.rotate_newly_activated_traps(this.syndrome_rotation_index);
    this.last_syndrome_bitstring = normalizedSeed;
  }

  public get_resource_index(logicalIndex: number): number {
    if (this.permutation_shard_a.length === 0) return 0;
    const boundedIndex = Math.abs(Math.trunc(logicalIndex)) % this.permutation_shard_a.length;
    return this.get_resource_index_from_shards(boundedIndex) % Math.max(1, this.agents.length);
  }

  public get_metacognitive_telemetry(): MetacognitiveTelemetry {
    return {
      self_awareness: this.prediction_accuracy,
      metacognitive_depth: this.state_history.length,
      is_predicting_disturbance: (this.last_prediction?.phi_integrated ?? 1) < this.phi_degradation_threshold || (this.last_prediction?.syndrome_pressure ?? 0) > this.syndrome_pressure_limit,
      prediction_accuracy: this.prediction_accuracy,
      events: [...this.metacognitive_events],
      strategy_weights: Object.fromEntries([...this.strategy_weights.entries()].map(([syndrome, weight]) => [String(syndrome), weight])),
    };
  }

  public inject_state_history_for_test(history: MetacognitiveStateVector[]): void {
    this.state_history = history.slice(-100).map((state) => ({ ...state }));
    this.last_prediction = null;
  }

  public simulate_intrusion_for_test(
    syndromeSeed: number,
    outcome: Pick<MetacognitiveStateVector, 'phi_integrated'> & Partial<MetacognitiveStateVector>,
  ): void {
    this.last_syndrome_bitstring = Math.trunc(syndromeSeed) >>> 0;
    this.last_syndrome = {
      ...this.last_syndrome,
      syndrome_weight: Math.max(0, Math.round((outcome.syndrome_pressure ?? 0.25) * this.syndrome_width)),
      confidence: clamp01(outcome.confidence_delta === undefined ? 0.99 : 1 - Math.abs(outcome.confidence_delta)),
    };
    this.state_history.push({
      phi_integrated: clamp01(outcome.phi_integrated),
      syndrome_pressure: clamp01(outcome.syndrome_pressure ?? 0.1),
      shard_entropy: clamp01(outcome.shard_entropy ?? this.calculate_shard_entropy()),
      confidence_delta: clamp01(outcome.confidence_delta ?? 0.01),
      resource_exhaustion: clamp01(outcome.resource_exhaustion ?? this.calculate_resource_exhaustion()),
    });
    if (this.state_history.length > 100) this.state_history.shift();
  }

  public get_strategy_weight(syndromeSeed: number): number {
    return this.strategy_weights.get(Math.trunc(syndromeSeed) >>> 0) || 1.0;
  }

  private get_sampled_ancillas(): SwarmAgent[] {
    const activeAncillas = this.agents.filter((agent) => agent.role === 'ancilla' && agent.state === 'active');
    if (this.operating_mode === 'NORMAL') return activeAncillas.slice(0, this.syndrome_width);
    return activeAncillas.filter((_, index) => (index + this.syndrome_round) % this.syndrome_check_stride === 0).slice(0, this.syndrome_width);
  }

  private capture_state_vector(): MetacognitiveStateVector {
    const syndromeCapacity = Math.max(1, this.last_syndrome.sampled_ancillas || this.syndrome_width);
    const syndrome_pressure = clamp01(
      this.last_syndrome.syndrome_weight / syndromeCapacity + this.last_syndrome.trap_disturbances / Math.max(1, this.reserved_trap_pool),
    );
    const confidence_delta = this.state_history.length ? Math.abs(this.last_syndrome.confidence - this.state_history[this.state_history.length - 1].phi_integrated) : 0;
    const resource_exhaustion = this.calculate_resource_exhaustion();
    return {
      phi_integrated: clamp01(this.last_syndrome.confidence * (1 - syndrome_pressure * 0.5) * (1 - resource_exhaustion * 0.25)),
      syndrome_pressure,
      shard_entropy: this.calculate_shard_entropy(),
      confidence_delta: clamp01(confidence_delta),
      resource_exhaustion,
    };
  }

  private predict_next_state(): MetacognitiveStateVector {
    const current = this.capture_state_vector();
    if (this.state_history.length < 2) return current;
    const recent = this.state_history.slice(-6);
    const deltas = recent.slice(1).map((state, index) => this.state_delta(recent[index], state));
    const averageDelta = deltas.reduce<MetacognitiveStateVector>(
      (acc, delta) => ({
        phi_integrated: acc.phi_integrated + delta.phi_integrated,
        syndrome_pressure: acc.syndrome_pressure + delta.syndrome_pressure,
        shard_entropy: acc.shard_entropy + delta.shard_entropy,
        confidence_delta: acc.confidence_delta + delta.confidence_delta,
        resource_exhaustion: acc.resource_exhaustion + delta.resource_exhaustion,
      }),
      { phi_integrated: 0, syndrome_pressure: 0, shard_entropy: 0, confidence_delta: 0, resource_exhaustion: 0 },
    );
    const scale = 1 / Math.max(1, deltas.length);
    const base = recent[recent.length - 1] || current;
    return {
      phi_integrated: clamp01(base.phi_integrated + averageDelta.phi_integrated * scale),
      syndrome_pressure: clamp01(base.syndrome_pressure + averageDelta.syndrome_pressure * scale),
      shard_entropy: clamp01(base.shard_entropy + averageDelta.shard_entropy * scale),
      confidence_delta: clamp01(base.confidence_delta + averageDelta.confidence_delta * scale),
      resource_exhaustion: clamp01(base.resource_exhaustion + averageDelta.resource_exhaustion * scale),
    };
  }

  private state_delta(previous: MetacognitiveStateVector, next: MetacognitiveStateVector): MetacognitiveStateVector {
    return {
      phi_integrated: next.phi_integrated - previous.phi_integrated,
      syndrome_pressure: next.syndrome_pressure - previous.syndrome_pressure,
      shard_entropy: next.shard_entropy - previous.shard_entropy,
      confidence_delta: next.confidence_delta - previous.confidence_delta,
      resource_exhaustion: next.resource_exhaustion - previous.resource_exhaustion,
    };
  }

  private update_prediction_accuracy(current: MetacognitiveStateVector): void {
    if (!this.last_prediction) return;
    const squaredError =
      (this.last_prediction.phi_integrated - current.phi_integrated) ** 2 +
      (this.last_prediction.syndrome_pressure - current.syndrome_pressure) ** 2 +
      (this.last_prediction.shard_entropy - current.shard_entropy) ** 2 +
      (this.last_prediction.confidence_delta - current.confidence_delta) ** 2 +
      (this.last_prediction.resource_exhaustion - current.resource_exhaustion) ** 2;
    const accuracy = clamp01(1 - squaredError / 5);
    this.prediction_accuracy = clamp01(this.prediction_accuracy * 0.9 + accuracy * 0.1);
  }

  private calculate_metacognitive_entropy(current: MetacognitiveStateVector, predicted: MetacognitiveStateVector): number {
    const phiError = Math.abs(predicted.phi_integrated - current.phi_integrated);
    const pressureError = Math.abs(predicted.syndrome_pressure - current.syndrome_pressure);
    return (Math.trunc(phiError * 1_000_000) ^ Math.trunc(pressureError * 1_000_000) ^ this.last_syndrome_bitstring ^ Math.trunc(this.prediction_accuracy * 65_535)) >>> 0;
  }

  private reinforce_successful_patterns(state: MetacognitiveStateVector): void {
    const syndrome = this.last_syndrome_bitstring >>> 0;
    const currentWeight = this.strategy_weights.get(syndrome) || 1.0;
    const preservedPhi = state.phi_integrated * this.last_syndrome.confidence > 0.8;
    const multiplier = preservedPhi ? 1 + this.metacognitive_learning_rate : 1 - this.metacognitive_learning_rate;
    this.strategy_weights.set(syndrome, Math.max(0.1, Math.min(10, currentWeight * multiplier)));
  }

  private calculate_resource_exhaustion(): number {
    const activeAncillas = this.agents.filter((agent) => agent.role === 'ancilla' && agent.state === 'active').length;
    return clamp01(activeAncillas / Math.max(1, this.max_ancilla_pool));
  }

  private calculate_shard_entropy(): number {
    if (this.permutation_shard_a.length === 0) return 0;
    const buckets = new Map<number, number>();
    for (let i = 0; i < this.permutation_shard_a.length; i++) {
      const bucket = this.get_resource_index_from_shards(i) % Math.max(1, this.agents.length);
      buckets.set(bucket, (buckets.get(bucket) || 0) + 1);
    }
    let entropy = 0;
    for (const count of buckets.values()) {
      const probability = count / this.permutation_shard_a.length;
      entropy -= probability * Math.log2(probability);
    }
    return clamp01(entropy / Math.log2(Math.max(2, this.permutation_shard_a.length)));
  }

  private log_metacognitive_event(event: string): void {
    this.metacognitive_events.push(event);
    if (this.metacognitive_events.length > 32) this.metacognitive_events.shift();
  }

  private evaluate_ancilla_exhaustion(): void {
    if (this.operating_mode === 'SANITIZED') return;
    
    const reservedAncillas = this.agents.filter((agent) => agent.role === 'ancilla' && agent.state === 'reserved').length;
    const reserveRatio = reservedAncillas / Math.max(1, this.max_ancilla_pool);

    if (reserveRatio < this.exhausted_pool_ratio) {
      this.set_operating_mode('EXHAUSTED', 10, 0.1);
      return;
    }

    if (reserveRatio < this.compressed_pool_ratio) {
      this.set_operating_mode('COMPRESSED', 2, 0.5);
      return;
    }

    this.set_operating_mode('NORMAL', 1, 1.0);
  }

  private set_operating_mode(mode: OperatingMode, stride: number, frequency: number): void {
    this.operating_mode = mode;
    this.syndrome_check_stride = stride;
    this.check_frequency = frequency;
    if (mode !== 'NORMAL') {
      this.last_syndrome = {
        ...this.last_syndrome,
        anomaly_detected: true,
        cause: 'resource_exhaustion',
        operating_mode: mode,
        check_frequency: frequency,
      };
    }
  }

  private encode_syndrome_bitstring(syndrome: Array<0 | 1>): number {
    return syndrome.reduce<number>((acc, bit, index) => acc | (bit << index), 0);
  }

  private derive_clifford_index(syndromeBitstring: number): number {
    const hammingWeight = syndromeBitstring.toString(2).split('').filter((bit) => bit === '1').length;
    return ((hammingWeight * 0xdeadbeef) ^ syndromeBitstring) % 24;
  }

  private initialize_holographic_pool(): void {
    const identityPermutation = this.agents.map((_, index) => index);
    this.store_permutation_as_shards(identityPermutation, 0x1337);
  }

  private update_permutation_shards(syndromeBitstring: number): void {
    const nextPermutation = this.derive_deterministic_shuffle(syndromeBitstring);
    this.store_permutation_as_shards(nextPermutation, syndromeBitstring);
  }

  private derive_deterministic_shuffle(syndromeBitstring: number): number[] {
    const learnedBias = this.strategy_weights.get(syndromeBitstring >>> 0) || 1.0;
    const biasedSyndrome = (syndromeBitstring ^ Math.trunc(learnedBias * 10_000)) >>> 0;
    const nextPermutation = Array.from({ length: this.agents.length }, (_, logicalIndex) => this.get_resource_index_from_shards(logicalIndex));
    for (let i = nextPermutation.length - 1; i > 0; i--) {
      const swapIndex = Math.abs((biasedSyndrome ^ (i * 31)) % (i + 1));
      [nextPermutation[i], nextPermutation[swapIndex]] = [nextPermutation[swapIndex], nextPermutation[i]];
    }
    return nextPermutation;
  }

  private store_permutation_as_shards(permutation: number[], syndromeBitstring: number): void {
    this.permutation_shard_a = new Uint32Array(permutation.length);
    this.permutation_shard_b = new Uint32Array(permutation.length);
    for (let i = 0; i < permutation.length; i++) {
      const mask = this.derive_shard_mask(syndromeBitstring, i);
      this.permutation_shard_a[i] = mask;
      this.permutation_shard_b[i] = (permutation[i] ^ mask) >>> 0;
    }
    this.pool_permutation_checksum = this.calculate_permutation_checksum();
  }

  private derive_shard_mask(syndromeBitstring: number, index: number): number {
    const syndromeDomain = ((syndromeBitstring * 2_654_435_761) ^ (index * 2_246_822_519) ^ 0x9e3779b9) >>> 0;
    return (syndromeDomain ^ this.crypto_uint32()) >>> 0;
  }

  private crypto_uint32(): number {
    return randomBytes(4).readUInt32BE(0);
  }

  private get_resource_index_from_shards(logicalIndex: number): number {
    return (this.permutation_shard_a[logicalIndex] ^ this.permutation_shard_b[logicalIndex]) >>> 0;
  }

  private calculate_permutation_checksum(): number {
    let checksum = 0;
    for (let i = 0; i < this.permutation_shard_a.length; i++) {
      checksum = (checksum + (i + 1) * (this.get_resource_index_from_shards(i) + 1)) % 1_000_003;
    }
    return checksum;
  }

  private evaluate_trap_sanitization(): void {
    const activeTraps = this.agents.filter((agent) => agent.role === 'trap' && agent.state === 'active').length;
    const reservedTraps = this.agents.filter((agent) => agent.role === 'trap' && agent.state === 'reserved').length;
    if (activeTraps === 0 && reservedTraps === 0 && !this.sanitized) {
      this.sanitized = true;
      this.operating_mode = 'SANITIZED';
      for (let i = 0; i < this.permutation_shard_a.length; i++) {
        this.permutation_shard_a[i] = this.crypto_uint32();
        this.permutation_shard_b[i] = this.crypto_uint32();
      }
      this.pool_permutation_checksum = 0;
      this.last_syndrome = {
        ...this.last_syndrome,
        anomaly_detected: true,
        cause: 'resource_exhaustion',
        operating_mode: this.operating_mode,
      };
    }
  }

  private rotate_newly_activated_traps(rotationIndex: number): void {
    const phaseShift = project_to_phi_floor((rotationIndex + 1) * PHI);
    for (const trap of this.agents.filter((agent) => agent.role === 'trap' && agent.state === 'active' && !agent.trap_disturbed)) {
      trap.phase = project_to_phi_floor(trap.phase + phaseShift);
    }
  }

  private activate_reserved(role: AgentRole, requested: number): number {
    let activated = 0;
    for (let logicalIndex = 0; logicalIndex < this.permutation_shard_a.length; logicalIndex++) {
      const agentIndex = this.get_resource_index_from_shards(logicalIndex);
      const agent = this.agents[agentIndex];
      if (!agent || agent.role !== role || agent.state !== 'reserved') continue;
      if (activated >= requested) break;
      agent.state = 'active';
      agent.trap_disturbed = false;
      agent.syndrome_bit = 0;
      agent.entropy = 0;
      activated += 1;
    }
    return activated;
  }

  private active_agents_count(): number {
    return this.agents.filter((agent) => agent.state === 'active').length;
  }

  public get_swarm_status(): SecuritySwarmStatus {
    const byRoleAndState = (role: AgentRole, state?: AgentState): number =>
      this.agents.filter((agent) => agent.role === role && (state ? agent.state === state : true)).length;

    return {
      agents_total: this.agents.length,
      agents_active: this.active_agents_count(),
      logical_agents: byRoleAndState('logical'),
      reserved_ancillas: byRoleAndState('ancilla', 'reserved'),
      active_ancillas: byRoleAndState('ancilla', 'active'),
      reserved_traps: byRoleAndState('trap', 'reserved'),
      active_traps: byRoleAndState('trap', 'active'),
      disturbed_traps: this.agents.filter((agent) => agent.role === 'trap' && agent.trap_disturbed).length,
      retired_traps: byRoleAndState('trap', 'retired'),
      integrity_locked: !this.last_syndrome.anomaly_detected && this.last_syndrome.confidence >= this.confidence_threshold,
      confidence_threshold: this.confidence_threshold,
      syndrome_width: this.syndrome_width,
      last_syndrome_weight: this.last_syndrome.syndrome_weight,
      last_confidence: this.last_syndrome.confidence,
      anomaly_detected: this.last_syndrome.anomaly_detected,
      response_cause: this.last_syndrome.cause,
      operating_mode: this.operating_mode,
      syndrome_check_stride: this.syndrome_check_stride,
      check_frequency: this.check_frequency,
      max_ancilla_pool: this.max_ancilla_pool,
      syndrome_rotation_index: this.syndrome_rotation_index,
      pool_permutation_checksum: this.pool_permutation_checksum,
      sanitized: this.sanitized,
      metacognitive: this.get_metacognitive_telemetry(),
    };
  }
}

export { SecuritySwarmAgent };
export const securitySwarms = new SecuritySwarmAgent();
