# Testing Guide

## Overview

This guide covers testing practices, coverage requirements, and recommendations for the HYBA_FULLSTACK repository. The project uses a mixed testing strategy with pytest for Python code and Vitest for TypeScript/JavaScript code.

## Test Structure

### Python Tests
- **Location**: `tests/` directory
- **Framework**: pytest with Hypothesis for property-based testing
- **Coverage areas**:
  - Mathematical invariants (golden ratio, HENDRIX-Φ solver)
  - Mining core logic (PULVINI compression, Stratum integration)
  - API endpoints and authentication
  - Reflexive optimization loop
  - Database models and migrations

### TypeScript Tests
- **Location**: `tests/**/*.test.ts`
- **Framework**: Vitest with fast-check for property-based testing
- **Coverage areas**:
  - Frontend components
  - API client logic
  - Bridge/server integration
  - TypeScript type safety

## Running Tests

### Python Tests
```bash
# Run all Python tests
npm run test:backend

# Run specific test file
pytest tests/test_golden_ratio_scaling.py

# Run with coverage
pytest --cov=python_backend --cov-report=html
```

### TypeScript Tests
```bash
# Run all TypeScript tests
npm run test:bridge

# Run property-based tests
npm run test:property:frontend

# Run with coverage
npm run test:bridge -- --coverage
```

### Production Gate
```bash
# Run full production gate (build, audit, test)
npm run prod:check
```

## Coverage Requirements

### Current Coverage Status
The repository maintains extensive test coverage across both Python and TypeScript codebases. Coverage reports are generated in `coverage.xml` and `htmlcov/`.

### Target Coverage Metrics
- **Python Backend**: Minimum 80% line coverage
- **TypeScript Frontend**: Minimum 75% line coverage
- **Critical Paths**: 100% coverage for mining core, authentication, and security-critical functions

### Critical Areas for Coverage
The following areas must have comprehensive test coverage:

1. **Mathematical Core**
   - Golden ratio library functions
   - HENDRIX-Φ solver logic
   - PULVINI compression algorithms
   - Basis selection mechanisms

2. **Security-Critical Functions**
   - Authentication and authorization
   - JWT token validation
   - Password hashing (Argon2id)
   - Input validation and sanitization

3. **Mining Operations**
   - Stratum protocol handling
   - Share submission logic
   - Pool failover mechanisms
   - Nonce traversal algorithms

4. **API Endpoints**
   - All public API routes
   - Error handling and edge cases
   - Rate limiting
   - WebSocket handlers

## Test Coverage Recommendations

### 1. Expand Property-Based Testing
- Use Hypothesis (Python) and fast-check (TypeScript) more extensively
- Test mathematical invariants with random inputs
- Verify boundary conditions and edge cases
- Example: Test golden ratio properties with random Fibonacci sequences

### 2. Add Integration Tests
- Test end-to-end API workflows
- Verify database transaction integrity
- Test WebSocket communication patterns
- Validate Stratum pool integration with mock pools

### 3. Improve Error Path Coverage
- Test all exception handling paths
- Verify graceful degradation on failures
- Test timeout and retry logic
- Validate error messages and logging

### 4. Add Performance Regression Tests
- Benchmark critical mathematical operations
- Monitor API response times
- Track memory usage patterns
- Set performance thresholds in CI

### 5. Security-Focused Testing
- Add fuzzing tests for input validation
- Test SQL injection prevention
- Verify XSS protection in frontend
- Test authentication bypass scenarios

### 6. Add Contract Tests
- Test API contract compliance
- Verify Stratum protocol conformance
- Validate data structure invariants
- Test certificate generation and validation

## Continuous Integration

### Coverage in CI
- Coverage reports should be generated on every PR
- PRs should not decrease overall coverage
- Critical paths must maintain 100% coverage
- Coverage thresholds enforced in CI pipeline

### Automated Testing
- All tests run automatically on push/PR
- Parallel test execution for faster feedback
- Test results reported in PR comments
- Failed tests block merging

## Test Maintenance

### Regular Review
- Review test coverage monthly
- Identify untested critical paths
- Update tests for new features
- Remove obsolete tests

### Test Quality
- Tests should be independent and isolated
- Use fixtures and mocks appropriately
- Avoid brittle tests that break on minor changes
- Document complex test scenarios

### Documentation
- Document test purposes in docstrings
- Explain property-based test invariants
- Maintain test data and fixtures
- Keep test naming consistent and descriptive

## Specific Recommendations by Module

### Mathematical Core (pythia_mining/)
- Add property-based tests for all mathematical transforms
- Test numerical stability with edge cases
- Verify deterministic behavior across runs
- Test compression ratio guarantees

### API Layer (hyba_genesis_api/)
- Add integration tests for all endpoints
- Test authentication/authorization flows
- Verify rate limiting behavior
- Test WebSocket message handling

### Frontend (src/)
- Add component unit tests
- Test user interaction flows
- Verify error handling in UI
- Test API client error scenarios

### Database (migrations/)
- Test migration rollback procedures
- Verify data integrity after migrations
- Test concurrent access patterns
- Validate foreign key constraints

## Tools and Resources

### Python Testing Tools
- **pytest**: Test framework
- **pytest-cov**: Coverage plugin
- **hypothesis**: Property-based testing
- **pytest-asyncio**: Async test support
- **factory-boy**: Test data generation

### TypeScript Testing Tools
- **vitest**: Test framework
- **@vitest/coverage-v8**: Coverage plugin
- **fast-check**: Property-based testing
- **msw**: API mocking
- **testing-library**: Component testing

### Coverage Analysis
- **coverage.py**: Python coverage reports
- **vitest coverage**: TypeScript coverage reports
- **codecov**: Coverage aggregation and visualization

## Best Practices

1. **Write tests alongside code**: Don't defer testing
2. **Keep tests fast**: Use mocks for slow dependencies
3. **Test behavior, not implementation**: Focus on what, not how
4. **Use descriptive test names**: Explain what is being tested
5. **One assertion per test**: Keep tests focused
6. **Arrange-Act-Assert pattern**: Structure tests clearly
7. **Avoid magic numbers**: Use named constants in tests
8. **Clean up after tests**: Ensure proper teardown

## Troubleshooting

### Common Issues

**Tests pass locally but fail in CI**
- Check environment differences
- Verify dependency versions match
- Ensure test data is committed
- Check for timing-dependent tests

**Coverage decreased after refactoring**
- Review removed test coverage
- Add tests for new code paths
- Verify tests weren't accidentally deleted
- Check for untested error paths

**Property-based tests find flaky failures**
- Review test assumptions
- Add constraints to input generation
- Check for non-deterministic behavior
- Increase test iterations if needed

## Future Improvements

1. **Add mutation testing**: Use tools like mutmut (Python) or stryker (JS)
2. **Implement contract testing**: Use Pact for API contract tests
3. **Add chaos engineering**: Test system resilience under failure
4. **Improve test data management**: Use factories and fixtures consistently
5. **Add visual regression testing**: For UI components
6. **Implement load testing**: For performance validation

## Conclusion

Maintaining high test coverage is critical for the reliability and security of the HYBA_FULLSTACK system. Regular review and expansion of test coverage ensures that new features are properly validated and existing functionality remains stable as the codebase evolves.
