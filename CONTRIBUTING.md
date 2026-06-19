# Contributing to HYBA_FULLSTACK

Thank you for your interest in contributing to HYBA_FULLSTACK! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

- Be respectful and inclusive in all interactions
- Focus on constructive feedback and collaboration
- Welcome newcomers and help them learn
- Respect differing viewpoints and experiences

## Getting Started

### Prerequisites
- Node.js 22.15.0+
- Python 3.12+
- Docker (optional, for containerized development)
- Git

### Setup Development Environment

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/HYBA_FULLSTACK.git
   cd HYBA_FULLSTACK
   ```

2. **Install Dependencies**
   ```bash
   # Frontend dependencies
   npm install
   
   # Python dependencies
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r python_backend/requirements.txt
   ```

3. **Configure Environment**
   ```bash
   cp .env.local.example .env.local
   # Edit .env.local with your local configuration
   ```

4. **Run Development Server**
   ```bash
   npm run dev
   ```

## Development Workflow

### Branch Strategy
- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - Feature branches
- `bugfix/*` - Bug fix branches
- `hotfix/*` - Critical production fixes

### Making Changes

1. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**
   - Write clean, readable code
   - Follow existing code style and patterns
   - Add tests for new functionality
   - Update documentation as needed

3. **Test Your Changes**
   ```bash
   # Run all tests
   npm run test:all
   
   # Run linting
   npm run lint
   ```

4. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

   Use conventional commit messages:
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation changes
   - `style:` - Code style changes (formatting, etc.)
   - `refactor:` - Code refactoring
   - `test:` - Test changes
   - `chore:` - Maintenance tasks

5. **Push and Create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

   Then create a pull request on GitHub with:
   - Clear description of changes
   - Related issue numbers
   - Testing performed
   - Screenshots for UI changes (if applicable)

## Code Style Guidelines

### TypeScript/JavaScript
- Use TypeScript for all new code
- Follow existing code patterns
- Use meaningful variable and function names
- Add JSDoc comments for complex functions
- Keep functions small and focused

### Python
- Follow PEP 8 style guide
- Use type hints where appropriate
- Write docstrings for all functions and classes
- Keep functions under 50 lines when possible
- Use meaningful variable names

### General
- Write self-documenting code
- Avoid magic numbers and strings
- Prefer composition over inheritance
- Keep dependencies minimal
- Write tests for edge cases

## Testing Guidelines

### Test Coverage
- Aim for >80% code coverage
- Write unit tests for individual functions
- Write integration tests for API endpoints
- Write E2E tests for critical user flows

### Test Structure
```python
# Python tests
def test_feature_name():
    # Arrange
    input_data = setup_test_data()
    
    # Act
    result = function_to_test(input_data)
    
    # Assert
    assert result.expected_value == actual_value
```

```typescript
// TypeScript tests
describe('FeatureName', () => {
  it('should do something', () => {
    // Arrange
    const input = createTestData();
    
    // Act
    const result = functionToTest(input);
    
    // Assert
    expect(result).toEqual(expectedValue);
  });
});
```

## Security Guidelines

### Never Commit Secrets
- Use environment variables for sensitive data
- Never commit API keys, passwords, or tokens
- Use `.env.local` for local development (already in `.gitignore`)
- Report security vulnerabilities privately

### Security Best Practices
- Validate all user inputs
- Use parameterized queries to prevent SQL injection
- Sanitize data before rendering
- Keep dependencies updated
- Follow OWASP security guidelines

## Documentation

### Code Documentation
- Add comments for complex logic
- Document public APIs
- Update README for user-facing changes
- Keep documentation in sync with code

### API Documentation
- Use OpenAPI/Swagger for REST APIs
- Document all endpoints
- Include request/response examples
- Document error responses

## Pull Request Review Process

### Before Submitting
- [ ] All tests pass
- [ ] Code follows style guidelines
- [ ] New features include tests
- [ ] Documentation is updated
- [ ] Commit messages follow conventions

### Review Criteria
- Code quality and maintainability
- Test coverage and quality
- Documentation completeness
- Security considerations
- Performance impact

### Addressing Feedback
- Respond to all review comments
- Make requested changes promptly
- Ask for clarification if needed
- Be open to suggestions

## Getting Help

### Resources
- Check existing documentation in `docs/`
- Review test files for usage examples
- Search existing GitHub issues
- Check the development workflow: `.devin/workflows/development.md`

### Contact
- Open a GitHub issue for bugs or feature requests
- Contact security team for security issues: security@hyba.ai
- Join community discussions (if available)

## Release Process

### Versioning
- Follow Semantic Versioning (MAJOR.MINOR.PATCH)
- MAJOR: Breaking changes
- MINOR: New features, backward compatible
- PATCH: Bug fixes, backward compatible

### Release Checklist
- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version number updated
- [ ] Release notes prepared
- [ ] Security review completed for sensitive changes

## License

By contributing to HYBA_FULLSTACK, you agree that your contributions will be licensed under the MIT License.

## Acknowledgments

Thank you for contributing to HYBA_FULLSTACK! Your contributions help make this project better for everyone.
