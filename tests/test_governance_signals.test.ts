import { describe, it, expect } from 'vitest';
import { buildGovernanceSignals } from '../src/governance';

/**
 * Unit tests for buildGovernanceSignals. These tests exercise the
 * decision logic for each governance signal under various inputs.
 */
describe('buildGovernanceSignals', () => {
  it('runtime-readiness passes when runtime is good and backend is connected', () => {
    const signals = buildGovernanceSignals({ runtimeStatus: 'ok', backendConnected: true });
    const runtimeSignal = signals.find(s => s.id === 'runtime-readiness');
    expect(runtimeSignal?.status).toBe('pass');
  });

  it('runtime-readiness fails when runtime is not good or backend is disconnected', () => {
    // runtime not good
    let signals = buildGovernanceSignals({ runtimeStatus: 'unhealthy', backendConnected: true });
    let runtimeSignal = signals.find(s => s.id === 'runtime-readiness');
    expect(runtimeSignal?.status).toBe('fail');

    // backend not connected
    signals = buildGovernanceSignals({ runtimeStatus: 'ok', backendConnected: false });
    runtimeSignal = signals.find(s => s.id === 'runtime-readiness');
    expect(runtimeSignal?.status).toBe('fail');
  });

  it('real-telemetry passes when telemetry source is non-synthetic', () => {
    const signals = buildGovernanceSignals({ telemetrySource: 'observability' });
    const s = signals.find(s => s.id === 'real-telemetry');
    expect(s?.status).toBe('pass');
  });

  it('real-telemetry fails when telemetry source includes synthetic or mock', () => {
    let signals = buildGovernanceSignals({ telemetrySource: 'synthetic-data' });
    let s = signals.find(sig => sig.id === 'real-telemetry');
    expect(s?.status).toBe('fail');
    signals = buildGovernanceSignals({ telemetrySource: 'mock_source' });
    s = signals.find(sig => sig.id === 'real-telemetry');
    expect(s?.status).toBe('fail');
  });

  it('pool-operator-gate passes only when an active pool or active name is present', () => {
    // active pool count > 0
    let signals = buildGovernanceSignals({ activePoolCount: 1 });
    let s = signals.find(sig => sig.id === 'pool-operator-gate');
    expect(s?.status).toBe('pass');

    // active pool name defined
    signals = buildGovernanceSignals({ activePoolName: 'pool-one' });
    s = signals.find(sig => sig.id === 'pool-operator-gate');
    expect(s?.status).toBe('pass');

    // configured pools but none active
    signals = buildGovernanceSignals({ configuredPoolCount: 2, activePoolCount: 0 });
    s = signals.find(sig => sig.id === 'pool-operator-gate');
    expect(s?.status).toBe('warn');

    // no configured pools
    signals = buildGovernanceSignals({ configuredPoolCount: 0, activePoolCount: 0 });
    s = signals.find(sig => sig.id === 'pool-operator-gate');
    expect(s?.status).toBe('fail');
  });

  it('security-posture fails when threat or security status is severe, passes when status exists, warns when missing', () => {
    // failure for critical threat level
    let signals = buildGovernanceSignals({ threatLevel: 'critical' });
    let s = signals.find(sig => sig.id === 'security-posture');
    expect(s?.status).toBe('fail');

    // failure for high security status
    signals = buildGovernanceSignals({ securityStatus: 'high' });
    s = signals.find(sig => sig.id === 'security-posture');
    expect(s?.status).toBe('fail');

    // pass when security status is ok
    signals = buildGovernanceSignals({ securityStatus: 'ok' });
    s = signals.find(sig => sig.id === 'security-posture');
    expect(s?.status).toBe('pass');

    // warn when security status is missing
    signals = buildGovernanceSignals({});
    s = signals.find(sig => sig.id === 'security-posture');
    expect(s?.status).toBe('warn');
  });

  it('claim-boundary passes when governance tags include no_unattended_writes or proposal_only; warns otherwise', () => {
    // pass for no_unattended_writes tag
    let signals = buildGovernanceSignals({ governanceTags: ['no_unattended_writes'] });
    let s = signals.find(sig => sig.id === 'claim-boundary');
    expect(s?.status).toBe('pass');

    // pass for proposal_only tag
    signals = buildGovernanceSignals({ governanceTags: ['proposal_only'] });
    s = signals.find(sig => sig.id === 'claim-boundary');
    expect(s?.status).toBe('pass');

    // warn for missing tags
    signals = buildGovernanceSignals({});
    s = signals.find(sig => sig.id === 'claim-boundary');
    expect(s?.status).toBe('warn');
  });

  it('phi-evidence passes when phiResonance is finite; warns otherwise', () => {
    let signals = buildGovernanceSignals({ phiResonance: 0.5 });
    let s = signals.find(sig => sig.id === 'phi-evidence');
    expect(s?.status).toBe('pass');

    signals = buildGovernanceSignals({ phiResonance: undefined });
    s = signals.find(sig => sig.id === 'phi-evidence');
    expect(s?.status).toBe('warn');
  });
});
