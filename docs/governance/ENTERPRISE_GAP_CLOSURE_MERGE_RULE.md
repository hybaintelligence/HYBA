# Enterprise Gap Closure Merge Rule

Merge only when:

1. `enterprise-gap-closure-implementation` is updated against current `main`.
2. The command set in `docs/governance/ENTERPRISE_GAP_CLOSURE_COMMANDS.md` passes.
3. The generated `docs/governance/enterprise_gap_closure_gate.json` has `passed: true`.
4. Any non-repository external dependencies remain listed in `docs/governance/ENTERPRISE_GAP_CLOSURE_REMAINING_EXTERNAL_DEPENDENCIES.md`.

Parent: #130
