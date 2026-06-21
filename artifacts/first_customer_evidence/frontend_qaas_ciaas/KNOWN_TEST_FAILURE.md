# Known Non-QaaS/CIaaS Frontend Test Failure

## Status
Documented: 2026-06-21

## Test Failure Details
- **Total Frontend Tests**: 230
- **Passed**: 229
- **Failed**: 1
- **Failure Type**: Governance signals test
- **Related to QaaS/CIaaS**: No

## Impact Assessment
This test failure is:
- **Pre-existing**: Related to governance-signal work, not introduced by QaaS/CIaaS integration
- **Unrelated**: Does not affect QaaS/CIaaS manager functionality or privilege boundary enforcement
- **Tracked Separately**: Part of ongoing governance signal implementation work

## QaaS/CIaaS Evidence Integrity
The QaaS/CIaaS frontend integration evidence remains valid because:
1. All QaaS/CIaaS-specific functionality tests pass
2. Privilege boundary regression tests pass (newly added)
3. The failing test is in a separate domain (governance signals)
4. No QaaS/CIaaS code paths are affected by this failure

## Regression Tests Added
To ensure QaaS/CIaaS privilege boundary integrity, the following regression tests were added:
1. `test_frontend_privilege_boundary.test.ts` - Verifies non-admin users cannot access admin endpoints
2. Tests for QaaS customer vs admin endpoint separation
3. Tests for CIaaS customer vs admin endpoint separation
4. UI assertion tests for admin-only field visibility

## Next Steps
- Continue tracking governance signal test resolution separately
- No action required for QaaS/CIaaS first-customer readiness
- This documentation serves as evidence that the failure is unrelated to QaaS/CIaaS work
