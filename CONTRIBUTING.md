# Contributing to Salamander

Thank you for your interest in contributing to Salamander! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to uphold our [Code of Conduct](CODE_OF_CONDUCT.md).

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the [existing issues](https://github.com/yourorg/salamander/issues) as you might find that the problem has already been reported.

When creating a bug report, please include:

- **Clear title**: Describe the problem concisely
- **Reproduction steps**: Numbered list of steps to reproduce
- **Expected behavior**: What you expected to happen
- **Actual behavior**: What actually happened
- **Environment**: OS, Python version, Salamander version
- **Additional context**: Screenshots, logs, error messages

**Example**:
```markdown
## Bug: Regeneration fails with InnervationFailure when context is None

### Steps to Reproduce
1. Create a module state
2. Apply fault with severity 0.7
3. Call quarantine_channel
4. Call redifferentiate with context=None

### Expected Behavior
Should raise InnervationFailure with clear error message

### Actual Behavior
Raises vague error: "No context signal available"

### Environment
- OS: Ubuntu 22.04
- Python: 3.9.6
- Salamander: 1.0.0
```

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

- **Clear use case**: Who benefits and why
- **Proposed solution**: How you envision it working
- **Alternatives considered**: Other approaches you've thought about
- **Additional context**: Mockups, examples, references

### Pull Requests

#### Before You Start

1. **Check existing PRs**: Ensure no one else is working on the same thing
2. **Open an issue first**: Discuss the change with maintainers
3. **Keep it focused**: One feature/fix per PR
4. **Follow the style guide**: See below

#### Development Workflow

```bash
# 1. Fork the repository
# Click "Fork" on GitHub

# 2. Clone your fork
git clone https://github.com/yourusername/salamander.git
cd salamander

# 3. Create a branch
git checkout -b feature/my-new-feature

# 4. Make your changes
# ... edit files ...

# 5. Run tests
PYTHONPATH=python_backend python3 -m pytest tests/ -v

# 6. Run linters
flake8 python_backend/
prettier --check src/

# 7. Commit your changes
git add .
git commit -m "feat: add new feature"

# 8. Push to your fork
git push origin feature/my-new-feature

# 9. Open a Pull Request
# Go to GitHub and click "New Pull Request"
```

#### Pull Request Guidelines

- **Title**: Use conventional commits format:
  - `feat: add new feature`
  - `fix: fix bug in regeneration pipeline`
  - `docs: update API documentation`
  - `test: add tests for edge cases`
  - `refactor: simplify density matrix operations`
  - `perf: optimize Lindblad decay operator`

- **Description**: Include:
  - What changed and why
  - Link to related issue
  - Screenshots (if UI changes)
  - Test results
  - Breaking changes (if any)

- **Size**: Keep PRs under 400 lines when possible
- **Tests**: Add tests for new functionality
- **Documentation**: Update docs if needed

#### Code Review Process

1. **Automated checks**: CI/CD runs tests, linters, benchmarks
2. **Maintainer review**: At least one maintainer must approve
3. **Address feedback**: Make requested changes
4. **Approval and merge**: Maintainer merges when ready

## Development Setup

### Prerequisites

- Python 3.9+
- pip or poetry
- Git
- Virtual environment tool (venv, virtualenv, conda)

### Installation

```bash
# Clone repository
git clone https://github.com/yourorg/salamander.git
cd salamander

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### Project Structure

```
salamander/
├── python_backend/
│   ├── pythia_mining/
│   │   ├── stateful_regeneration.py  # Core regeneration engine
│   │   ├── consciousness_engine.py
│   │   ├── synaptic_persistence_layer.py
│   │   └── ...
│   └── hyba_genesis_api/
│       ├── api/
│       │   ├── security.py           # Security API with regeneration
│       │   ├── regeneration_router.py
│       │   └── multi_agent/          # Multi-agent system
│       └── ...
├── tests/
│   ├── test_quantum_regeneration_properties.py
│   ├── test_salamander_frontier.py
│   └── ...
├── docs/
│   ├── SCIENTIFIC_POSITION_SALAMANDER.md
│   ├── INDUSTRY_POSITION_SALAMANDER.md
│   └── ...
├── src/                              # Frontend (if applicable)
├── requirements.txt
├── requirements-dev.txt
├── pyproject.t