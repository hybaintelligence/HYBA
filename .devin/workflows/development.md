---
description: Common development workflow for HYBA_FULLSTACK project
---

# HYBA_FULLSTACK Development Workflow

## Overview
This workflow provides standardized procedures for common development tasks in the HYBA_FULLSTACK project.

## Prerequisites
- Node.js 22.15.0+
- Python 3.12+
- Docker (optional, for containerized development)

## Setup

### Initial Setup
```bash
# Install frontend dependencies
npm install

# Install Python dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r python_backend/requirements.txt
```

### Environment Configuration
```bash
# Copy example environment file
cp .env.local.example .env.local

# Edit with your local configuration
# IMPORTANT: Never commit .env.local to version control
```

## Development Workflow

### 1. Start Development Server
```bash
# Start both frontend and backend
npm run dev
```

This starts:
- Frontend Vite dev server on port 3000
- Python FastAPI backend on port 3001 (auto-spawned)

### 2. Run Tests
```bash
# Run all tests
npm run test:all

# Run only backend tests
npm run test:backend

# Run only frontend tests
npm run test:frontend:all

# Run property-based tests
npm run test:property
```

### 3. Code Quality Checks
```bash
# TypeScript type checking
npm run lint

# Python type checking (if using mypy)
mypy python_backend/

# Format code
npm run format  # If configured
black python_backend/
```

### 4. Build for Production
```bash
# Build frontend and backend
npm run build

# Build Docker image
docker build -t hyba-fullstack:local .
```

## Common Development Tasks

### Adding a New Feature
1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Run tests: `npm run test:all`
4. Run linting: `npm run lint`
5. Commit changes with descriptive messages
6. Push and create pull request

### Debugging Backend Issues
```bash
# Start backend in debug mode
cd python_backend
python -m uvicorn hyba_genesis_api.main:app --reload --host 127.0.0.1 --port 3001
```

### Debugging Frontend Issues
```bash
# Start frontend dev server with HMR
npm run dev
```

### Running Specific Test Suites
```bash
# Run mining-related tests
npm run test:mining:innovation

# Run intelligence fabric tests
npm run review:evidence:gate

# Run production readiness checks
npm run prod:local:gate
```

## Security Best Practices

### Never Commit Secrets
- Use `.env.local` for local development
- Use environment variables in production
- Never commit JWT secrets, API keys, or passwords

### Before Committing
```bash
# Check for accidentally committed secrets
git diff --cached | grep -i "secret\|password\|key"

# Run security checks
npm run security:scan  # If configured
```

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 3000
lsof -i :3000  # macOS/Linux
netstat -ano | findstr :3000  # Windows

# Kill the process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows
```

### Python Dependencies Issues
```bash
# Recreate virtual environment
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r python_backend/requirements.txt
```

### Frontend Build Errors
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

## Production Deployment

### Pre-Deployment Checklist
- [ ] All tests passing: `npm run test:all`
- [ ] No TypeScript errors: `npm run lint`
- [ ] Security scan passed
- [ ] Environment variables configured
- [ ] Docker build successful
- [ ] Production readiness gate passed: `npm run prod:local:gate`

### Deployment Steps
```bash
# Build production image
docker build -t hyba-fullstack:production .

# Tag for registry
docker tag hyba-fullstack:production registry.example.com/hyba-fullstack:latest

# Push to registry
docker push registry.example.com/hyba-fullstack:latest
```

## Getting Help

- Check documentation in `docs/` directory
- Review test files for usage examples
- Check GitHub Issues for known problems
- Contact security team for security issues: security@hyba.ai
