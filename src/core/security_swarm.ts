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
    const syndromePenalty =
      syndrome_weight / Math.max(1, activeAncillas.length || this.syndrome_width);
    const trapPenalty =
      trap_disturbances / Math.max(1, activeTraps.length || this.reserved_trap_pool);
    const confidence = clamp01(1 - syndromePenalty * 0.75 - trapPenalty * 0.25);
    const sampleCause: ResponseCause =
      trap_disturbances > 0
        ? "trap_disturbance"
        : syndrome_weight > this.syndrome_weight_threshold
          ? "syndrome_anomaly"
          : "none";

    // Preserve resource_exhaustion cause in degraded modes
    const cause: ResponseCause =
      this.operating_mode !== "NORMAL" && this.last_syndrome.cause === "resource_exhaustion"
        ? "resource_exhaustion"
        : sampleCause;

    this.last_syndrome = {
      syndrome,
      syndrome_weight,
      trap_disturbances,
      confidence,
      anomaly_detected: confidence < this.confidence_threshold || sampleCause !== "none",
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
    if (!this.sanitized) {
      this.update_permutation_shards(syndromeBitstring);
      this.syndrome_rotation_index = this.derive_clifford_index(syndromeBitstring);
    }
    const activated_ancillas = this.activate_reserved(
      "ancilla",
      Math.max(1, sample.syndrome_weight),
    );
    const activated_traps = this.activate_reserved(
      "trap",
      Math.max(1, retired_traps || sample.trap_disturbances),
    );
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

  private get_sampled_ancillas(): SwarmAgent[] {
    const activeAncillas = this.agents.filter((agent) => agent.role === 'ancilla' && agent.state === 'active');
    if (this.operating_mode === 'NORMAL') return activeAncillas.slice(0, this.syndrome_width);
    return activeAncillas.filter((_, index) => (index + this.syndrome_round) % this.syndrome_check_stride === 0).slice(0, this.syndrome_width);
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
    const nextPermutation = Array.from({ length: this.agents.length }, (_, logicalIndex) => this.get_resource_index(logicalIndex));
    for (let i = nextPermutation.length - 1; i > 0; i--) {
      const swapIndex = Math.abs((syndromeBitstring ^ (i * 31)) % (i + 1));
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

  private get_resource_index(logicalIndex: number): number {
    return (this.permutation_shard_a[logicalIndex] ^ this.permutation_shard_b[logicalIndex]) >>> 0;
  }

  private calculate_permutation_checksum(): number {
    let checksum = 0;
    for (let i = 0; i < this.permutation_shard_a.length; i++) {
      checksum = (checksum + (i + 1) * (this.get_resource_index(i) + 1)) % 1_000_003;
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
      const agentIndex = this.get_resource_index(logicalIndex);
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
    };
  }
}

export { SecuritySwarmAgent };
export const securitySwarms = new SecuritySwarmAgent();
