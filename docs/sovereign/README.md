# HYBA Sovereign Buyer Asset Pack

This directory turns the sovereign deployment work from narrative into versioned buyer and operator artefacts.

## Contents

1. [`SOVEREIGN_DEPLOYMENT_WHITEPAPER.md`](./SOVEREIGN_DEPLOYMENT_WHITEPAPER.md)
2. [`REGULATOR_GRADE_ARCHITECTURE_DIAGRAM.md`](./REGULATOR_GRADE_ARCHITECTURE_DIAGRAM.md)
3. [`SOVEREIGN_PROCUREMENT_POSITIONING.md`](./SOVEREIGN_PROCUREMENT_POSITIONING.md)
4. [`AIR_GAPPED_OPERATIONAL_READINESS_CHECKLIST.md`](./AIR_GAPPED_OPERATIONAL_READINESS_CHECKLIST.md)
5. [`NATIONAL_SECURITY_EXECUTIVE_BRIEFING.md`](./NATIONAL_SECURITY_EXECUTIVE_BRIEFING.md)
6. [`SOVEREIGN_REALITY_CHECK.md`](./SOVEREIGN_REALITY_CHECK.md)

## Code foundation

The asset pack is grounded in the implementation in:

- `python_backend/hyba_ciaas/ingestion.py`
- `python_backend/hyba_ciaas/sovereign_runtime.py`
- `tests/test_central_data_ingestion.py`
- `tests/test_sovereign_deployment_control_plane.py`

## Procurement-safe posture

HYBA provides technical enforcement surfaces for sovereign, regulated, on-premise, and air-gapped deployment assessment. Accreditation, certification, classified approval, and authority-to-operate remain customer, regulator, and environment-specific processes.

## Verification commands

```bash
pytest tests/test_central_data_ingestion.py -q
pytest tests/test_sovereign_deployment_control_plane.py -q
```
