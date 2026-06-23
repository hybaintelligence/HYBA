# HYBA Sovereign Buyer Asset Pack

This directory turns the sovereign deployment work from narrative into versioned buyer and operator artefacts.

## Contents

1. [`SOVEREIGN_DEPLOYMENT_WHITEPAPER.md`](./SOVEREIGN_DEPLOYMENT_WHITEPAPER.md)
2. [`REGULATOR_GRADE_ARCHITECTURE_DIAGRAM.md`](./REGULATOR_GRADE_ARCHITECTURE_DIAGRAM.md)
3. [`SOVEREIGN_PROCUREMENT_POSITIONING.md`](./SOVEREIGN_PROCUREMENT_POSITIONING.md)
4. [`AIR_GAPPED_OPERATIONAL_READINESS_CHECKLIST.md`](./AIR_GAPPED_OPERATIONAL_READINESS_CHECKLIST.md)
5. [`NATIONAL_SECURITY_EXECUTIVE_BRIEFING.md`](./NATIONAL_SECURITY_EXECUTIVE_BRIEFING.md)
6. [`SOVEREIGN_REALITY_CHECK.md`](./SOVEREIGN_REALITY_CHECK.md)
7. [`PRODUCTION_READINESS_COMPLETION_PLAN.md`](./PRODUCTION_READINESS_COMPLETION_PLAN.md)

## Code foundation

The asset pack is grounded in the implementation in:

- `python_backend/hyba_ciaas/ingestion.py`
- `python_backend/hyba_ciaas/sovereign_runtime.py`
- `tests/test_central_data_ingestion.py`
- `tests/test_sovereign_deployment_control_plane.py`
- `scripts/sovereign_readiness_gate.py`
- `.github/workflows/sovereign-readiness.yml`

## Procurement-safe posture

HYBA provides technical enforcement surfaces for sovereign, regulated, on-premise, and air-gapped deployment assessment. Accreditation, certification, classified approval, and authority-to-operate remain customer, regulator, and environment-specific processes.

## Verification commands

```bash
PYTHONPATH=python_backend pytest tests/test_central_data_ingestion.py -q
PYTHONPATH=python_backend pytest tests/test_sovereign_deployment_control_plane.py -q
PYTHONPATH=python_backend python scripts/sovereign_readiness_gate.py
```

## Production readiness status

The sovereign foundation is implemented and merged. It should not be described as production-ready for a named customer deployment until the production gates in `PRODUCTION_READINESS_COMPLETION_PLAN.md` are green and the air-gapped operational checklist has been executed in the target environment.
