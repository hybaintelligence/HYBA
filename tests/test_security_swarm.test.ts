import { describe, expect, it } from "vitest";
import fc from "fast-check";
import { SecuritySwarmAgent } from "../src/core/security_swarm";

describe("HYBA stabilizer integrity monitor", () => {
  it("keeps the stabilizer monitor locked without disturbance", () => {
    const monitor = new SecuritySwarmAgent();
    const sample = monitor.monitor_integrity(0);
    const status = monitor.get_swarm_status();

    expect(sample.syndrome_weight).toBe(0);
    expect(sample.trap_disturbances).toBe(0);
    expect(sample.confidence).toBeGreaterThanOrEqual(status.confidence_threshold);
    expect(sample.anomaly_detected).toBe(false);
    expect(status.integrity_locked).toBe(true);
    expect(status.operating_mode).toBe("NORMAL");
  });

  it("treats non-zero syndromes and trap disturbance as anomaly signals, not attacker attribution", () => {
    const monitor = new SecuritySwarmAgent();
    const response = monitor.trigger_response(1);
    const status = monitor.get_swarm_status();

    expect(response.status).toBe("integrity_response_active");
    expect(["syndrome_anomaly", "trap_disturbance"]).toContain(response.cause);
    expect(response.note).toContain("no logical quantum state is cloned");
    expect(status.anomaly_detected).toBe(true);
    expect(status.integrity_locked).toBe(false);
  });

  it("activates only pre-allocated ancillas/traps instead of multiplying copies", () => {
    const monitor = new SecuritySwarmAgent();
    const before = monitor.get_swarm_status();
    const response = monitor.trigger_response(1);
    const after = monitor.get_swarm_status();

    expect(after.agents_total).toBe(before.agents_total);
    expect(after.logical_agents).toBe(1);
    expect(response.activated_ancillas + response.activated_traps).toBeGreaterThan(0);
    expect(after.reserved_ancillas + after.active_ancillas).toBe(before.reserved_ancillas + before.active_ancillas);
    expect(after.reserved_traps + after.active_traps + after.retired_traps).toBe(before.reserved_traps + before.active_traps + before.retired_traps);
  });

  it("uses syndrome bits as a deterministic Clifford phase index and pool shuffle", () => {
    const first = new SecuritySwarmAgent();
    const second = new SecuritySwarmAgent();
    const firstResponse = first.trigger_response(1);
    const secondResponse = second.trigger_response(1);
    const firstStatus = first.get_swarm_status();
    const secondStatus = second.get_swarm_status();

    expect(firstResponse.syndrome_rotation_index).toBeGreaterThanOrEqual(0);
    expect(firstResponse.syndrome_rotation_index).toBeLessThan(24);
    expect(firstStatus.syndrome_rotation_index).toBe(firstResponse.syndrome_rotation_index);
    expect(firstStatus.syndrome_rotation_index).toBe(secondStatus.syndrome_rotation_index);
    expect(firstStatus.pool_permutation_checksum).toBe(secondStatus.pool_permutation_checksum);
    expect(firstStatus.sanitized).toBe(false);
  });

  it("sanitizes the holographic pool when all trap resources are exhausted", () => {
    const monitor = new SecuritySwarmAgent();

    for (let i = 0; i < 8; i++) {
      monitor.trigger_response(1);
    }

    const status = monitor.get_swarm_status();
    expect(status.operating_mode).toBe("SANITIZED");
    expect(status.sanitized).toBe(true);
    expect(status.pool_permutation_checksum).toBe(0);
  });

  it("enters compressed or exhausted mode when finite ancilla resources are depleted", () => {
    const monitor = new SecuritySwarmAgent();

    for (let i = 0; i < 8; i++) {
      monitor.trigger_response(1);
    }

    const status = monitor.get_swarm_status();
    const sample = monitor.monitor_integrity(0);

    expect(["COMPRESSED", "EXHAUSTED", "SANITIZED"]).toContain(status.operating_mode);
    expect(status.response_cause).toBe("resource_exhaustion");
    expect(status.syndrome_check_stride).toBeGreaterThan(1);
    expect(status.check_frequency).toBeLessThan(1);
    expect(sample.sampled_ancillas).toBeLessThan(status.active_ancillas);
  });

  it("property: syndrome telemetry remains bounded for all disturbance probabilities", () => {
    fc.assert(
      fc.property(fc.float({ min: 0, max: 1, noNaN: true }), (disturbance) => {
        const monitor = new SecuritySwarmAgent();
        const sample = monitor.monitor_integrity(disturbance);

        expect(sample.confidence).toBeGreaterThanOrEqual(0);
        expect(sample.confidence).toBeLessThanOrEqual(1);
        expect(sample.syndrome_weight).toBeGreaterThanOrEqual(0);
        expect(sample.syndrome_weight).toBeLessThanOrEqual(sample.sampled_ancillas);
        expect(sample.trap_disturbances).toBeGreaterThanOrEqual(0);
      }),
      { numRuns: 50 }
    );
  });

  it("property: response never changes the pre-allocated resource budget", () => {
    fc.assert(
      fc.property(fc.array(fc.float({ min: 0, max: 1, noNaN: true }), { minLength: 1, maxLength: 12 }), (disturbances) => {
        const monitor = new SecuritySwarmAgent();
        const initial = monitor.get_swarm_status();

        for (const disturbance of disturbances) {
          monitor.trigger_response(disturbance);
        }

        const final = monitor.get_swarm_status();
        expect(final.agents_total).toBe(initial.agents_total);
        expect(final.logical_agents).toBe(1);
        expect(final.reserved_ancillas + final.active_ancillas).toBe(initial.reserved_ancillas + initial.active_ancillas);
        expect(final.reserved_traps + final.active_traps + final.retired_traps).toBe(initial.reserved_traps + initial.active_traps + initial.retired_traps);
      }),
      { numRuns: 30 }
    );
  });
});
