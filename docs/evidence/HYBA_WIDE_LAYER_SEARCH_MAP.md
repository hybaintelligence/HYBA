# HYBA wide layer search map

HYBA_FULLSTACK is one non-severable platform. This file records a wider repository search so the verification posture does not collapse into a narrow list of endpoints or into a mining-centred interpretation.

The rule is:

```text
many layers -> one platform substrate -> many verification windows
```

The proof API can expose separate interrogation windows, but those windows are not severable modules, detachable products, or separate mini-systems. They are projections of the same HYBA_FULLSTACK platform.

## Search method

This map was produced from broad repository search over layer, substrate, metabolic, Salamander, PULVINI, customer, portal, router, include_router, evidence, governance, deployment, security, FinOps, QaaS, CIaaS, quantum finance, observability, and runtime terms.

The search intentionally covered code, tests, artifacts, docs, frontend components, backend routers, scripts, benchmarks, and infrastructure evidence.

## Layer inventory discovered

| Layer / stratum | Search-backed evidence paths | Verification implication |
| --- | --- | --- |
| Platform substrate | `src/core/substrate.ts`; `python_backend/hyba_genesis_api/core/substrate.py`; `python_backend/hyba_genesis_api/core/substrate_interface.py`; `docs/HYBA_SUBSTRATE_POSITIONING.md`; `docs/THREE_SUBSTRATE_ARCHITECTURE.md`; `docs/SUBSTRATE_INDEPENDENCE.md`; `docs/FORMAL_PROOFS_SUBSTRATE_INDEPENDENCE.md`; `docs/QUANTUM_MATHEMATICS_SUBSTRATE_INDEPENDENCE.md` | The platform must be verified as a substrate first, not as a bundle of disconnected features. |
| Autonomic governance substrate | `docs/governance/autonomic-substrate-protocol.md`; `artifacts/GENESIS_PROTOCOL_FINAL_REPORT.md`; `scripts/first_self_optimization_event.py`; `tests/test_runtime_elevation_trace_packet.py` | Autonomy must remain bounded, auditable, and trace-packet evidenced. |
| API composition / routing | `python_backend/hyba_genesis_api/main.py`; `include_router(...)` call sites; `python_backend/hyba_genesis_api/api/*` routers | Routing proves many windows are mounted into one FastAPI platform, not separate apps. |
| Intelligence fabric | `python_backend/hyba_genesis_api/api/intelligence.py`; `python_backend/hyba_genesis_api/core/intelligence_fabric.py`; `src/core/intelligence_service.ts`; `src/core/intelligence_types.ts`; `src/core/emergent_intelligence.ts`; `src/core/predictive_intel.ts` | Intelligence claims need measured health, bounded semantics, and evidence-first checks. |
| AI orchestration layer | `python_backend/pythia_mining/ai_orchestration_layer.py`; `scripts/ablation_synaptic_layer.py`; `tests/test_intelligence_fabric.py`; `tests/test_reflexive_controller.py` | Orchestration must be shown as a platform layer, not as an ad-hoc mining assistant. |
| Synaptic persistence / memory layer | `python_backend/pythia_mining/synaptic_persistence_layer.py`; `cpp_core/synaptic_persistence.h`; `artifacts/memory_seed/memory_seed_v1.json` | Memory and persistence should be tested as platform state/capability layers. |
| PULVINI memory and mathematical layer | `scripts/pulvini_audit.py`; `scripts/generate_pulvini_manifest.py`; `python_backend/pythia_mining/pulvini_memory.py`; `python_backend/pythia_mining/pulvini_memory_fabric.py`; `python_backend/pythia_mining/pulvini_memory_compression_proof.py`; `python_backend/pythia_mining/pulvini_operator.py`; `python_backend/pythia_mining/pulvini_verifier.py`; `python_backend/pythia_mining/pulvini_tensor_network_integration.py`; `docs/scientific/PULVINI_FINAL_MATH_GATE.md` | PULVINI is broader than one endpoint and must be represented as memory/math/proof infrastructure. |
| φ / golden-ratio runtime layer | `scripts/phi_complete_stack_analysis.py`; `python_backend/pythia_mining/phi_oracle.py`; `python_backend/pythia_mining/phi_tuner.py`; `python_backend/pythia_mining/phi_fibonacci_lcg.py`; `cuda_core/phi_resonance.cu`; `src/core/phi_shield.ts` | φ claims must stay bounded to measured runtime, deterministic checks, and claim-tier boundaries. |
| Quantum substrate / operators layer | `python_backend/pythia_mining/mera_quantum.py`; `experiments/quantum_substrate_comparison.py`; `benchmarks/substrate_comparison.py`; `src/euclid/pythagoras/quantum/operators/pulvini_scaling.py`; `rust_core/src/lib.rs` | Quantum-related verification should distinguish substrate math, simulation, runtime execution, and product boundary. |
| QaaS / QIaaS execution layer | `python_backend/hyba_genesis_api/api/quantum_as_a_service.py`; `artifacts/salamander_integration/qaas_routes_integration.py`; `src/components/QaaSComputerManager.tsx`; `tests/test_quantum_as_a_service_api.py`; `tests/test_qiaas_integration_contract.py`; `docs/archive/2026-06/QAAS_INFRASTRUCTURE_ECOSYSTEM_GAP_ANALYSIS.md` | QaaS/QIaaS is an execution window into the platform, backed by route, component, and integration evidence. |
| CIaaS / computational-intelligence service layer | `python_backend/hyba_genesis_api/api/computational_intelligence_service.py`; `tests/test_commercial_public_api.py`; `tests/test_customer_commercial_api_contracts.py` | CIaaS must be verified through quotas, workload boundaries, customer keys, and tenant isolation. |
| Quantum finance layer | `python_backend/hyba_genesis_api/api/quantum_finance_service.py`; `tests/test_quantum_finance_service_design.py`; `docs/PYTHIA_FINANCE_SOVEREIGN_AUDIT_DEMO.md` | Finance-facing claims must remain bounded to API/service behaviour and must not become return/performance claims. |
| Customer/commercial access layer | `python_backend/hyba_genesis_api/api/customer_access.py`; `python_backend/hyba_genesis_api/api/customer_portal.py`; `src/components/CustomerPortal.tsx`; `tests/test_customer_portal_api.py`; `docs/runbooks/CUSTOMER_ONBOARDING.md` | Customer access must verify tenant isolation, onboarding, quota, auth, metering, and portal contracts. |
| Executive / operator control-plane layer | `src/components/CEOTerminal.tsx`; `tests/test_executive_integration.py`; `docs/ADMIN_PANEL_COMPLETE_AUDIT.md`; `python_backend/hyba_genesis_api/api/admin.py`; `python_backend/hyba_genesis_api/api/executive_router.py` | Operator control must be audited as a governance/control plane, not simply UI. |
| V4 metabolic / organism layer | `docs/V4_METABOLIC_ROUTER_SPECIFICATION.md`; `python_backend/hyba_genesis_api/api/metabolic_router.py`; `python_backend/hyba_genesis_api/api/organism_router.py`; `python_backend/pythia_mining/metabolism.py`; `python_backend/hyba_genesis_api/api/cognitive_schema.py` | Metabolic and organism metaphors must be bounded to route/API/runtime behaviours. |
| Salamander / regeneration layer | `python_backend/hyba_genesis_api/api/salamander_substrate.py`; `python_backend/hyba_genesis_api/api/regeneration_router.py`; `tests/test_salamander_substrate_api.py`; `tests/test_salamander_property_battery.py`; `tests/validation/test_salamander_physics.py`; `docs/archive/2026-06/SALAMANDER_INTEGRATION_IMPLEMENTATION_GUIDE.md`; `SALAMANDER_FORENSIC_AUDIT_REPORT.md` | Salamander/regeneration must be represented as a substrate verification layer with bounded scientific and API claims. |
| Mining / PYTHIA operational layer | `python_backend/pythia_mining/autonomous_mining_controller.py`; `python_backend/pythia_mining/main.py`; `docs/HYBA_MINING_DOCTRINE.md`; `tests/test_stratum_share_acceptance_e2e.py`; `tests/test_pool_handshake_contract.py`; `tests/test_mining_production_readiness_doctor.py` | Mining remains important, but only as one operational layer inside the platform. |
| Observability / telemetry layer | `python_backend/hyba_genesis_api/api/observability.py`; `python_backend/hyba_genesis_api/core/telemetry.py`; `src/core/telemetry.ts`; `artifacts/live_evidence/system_snapshot_1781884859.json`; `artifacts/production_lunch_run/frontend_health.txt` | Runtime claims must be backed by measurable telemetry and auditable artifacts. |
| Evidence / claim governance layer | `docs/evidence/CAPABILITY_CLAIM_LEDGER.md`; `docs/evidence/EVIDENCE_SOURCE_MAP.md`; `docs/evidence/KNOWN_LIMITATIONS_AND_NOT_TO_CLAIM.md`; `docs/evidence/EXTERNAL_REVIEW_WORKFLOW.md`; `docs/EXTERNAL_REVIEWER_PACK.md` | Extraordinary claims must map to claim tiers, evidence artifacts, and review workflow. |
| Testing / proof inventory layer | `artifacts/test_inventory/pytest_collect_final.txt`; `artifacts/test_inventory/pytest_collect_2628.txt`; `artifacts/production_lunch_run/test_inventory.txt`; `artifacts/frontend_api_command_manifest.generated.json`; `artifacts/frontend_api_command_coverage_status.json` | The proof system should be driven by real test inventory and command coverage, not manual summaries alone. |
| Security / compliance layer | `docs/security/ENTERPRISE_SECURITY_BASELINE.md`; `docs/compliance/SOC2_READINESS_EVIDENCE_MAP.md`; `docs/governance/GDPR_DATA_INVENTORY.md`; `scripts/validate_production_env.py`; `scripts/check_no_runtime_mocks.py`; `tests/test_auth_boundaries.py` | Security must be fail-closed and evidence-backed across auth, secrets, CORS, tenancy, privacy, and production gates. |
| FinOps / enterprise operating layer | `docs/finops/ENTERPRISE_FINOPS.md`; `docs/infrastructure/STANDARDIZATION_INTEROP.md`; `docs/performance/caching_and_rate_limiting.md`; `load_testing/locustfile.py` | Operational maturity includes cost, interoperability, performance, rate limits, and load behaviour. |
| Frontend platform layer | `src/App.tsx`; `src/apiClient.ts`; `src/swaggerSpec.ts`; `src/components/*`; `tests/test_frontend_backend_e2e.test.ts`; `tests/test_apiClient_core.test.ts`; `tests/test_apiClient_authInterceptor.test.ts` | Frontend is not cosmetic; it is a platform interaction and contract-verification layer. |
| Deployment / local production gate layer | `scripts/run_layered_deployment_gate.sh`; `scripts/local_production_gate.py`; `docs/PRODUCTION_READINESS.md`; `docs/PRODUCTION_READINESS_END_TO_END.md`; `artifacts/production_run_20260620_173257/git_status.txt`; `artifacts/production_lunch_run/git_status_after.txt` | Release confidence comes from local gates, deployment evidence, and reproducible commands. |
| Infrastructure / extension layer | `Dockerfile.prod`; `k8s-operator/Dockerfile`; `terraform-provider-hyba/internal/client/client.go`; `config/.env.docker` | Platform verification must include deployability, operator extension points, and infrastructure adapters. |

## Mapping rule for future proof endpoints

New proof endpoints should not be created as product slices. They should be created only when they expose a meaningful interrogation window into one of the layers above.

Every new window must answer:

```text
Which layer does this interrogate?
Which invariant does it test?
Which artifact records the evidence?
Which command reproduces it?
How does it map back to the one HYBA_FULLSTACK substrate?
```

## Minimum acceptance bar

A future proof catalogue is too narrow if it only covers mining, QaaS, CIaaS, governance, and observability.

A sufficiently wide proof catalogue must account for at least:

1. substrate
2. autonomic governance
3. API routing/composition
4. intelligence fabric
5. AI orchestration
6. synaptic persistence
7. PULVINI memory/math
8. φ/golden-ratio runtime
9. quantum substrate/operators
10. QaaS/QIaaS
11. CIaaS
12. quantum finance
13. commercial/customer access
14. executive/operator control-plane
15. metabolic/organism/cognitive-schema layer
16. Salamander/regeneration
17. mining/PYTHIA operations
18. observability/telemetry
19. evidence/claim governance
20. testing/proof inventory
21. security/compliance
22. FinOps/performance/interoperability
23. frontend contract/UI layer
24. deployment/local-production gate
25. infrastructure/extension layer

This is not a claim that all layers have equal maturity. It is a guard against under-describing HYBA_FULLSTACK. Search wide first; then classify evidence honestly as verified, evidence-linked, runtime-required, or limitation-bound.
