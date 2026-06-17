# Research Code Separation Plan

The HYBA_FULLSTACK repository contains both production services (e.g., FastAPI API, mining orchestration) and experimental or research modules (e.g., tensor network simulations, IIT analysis).  Mixing these concerns increases complexity and risk.  This plan outlines steps to separate research code from production code while preserving the ability to integrate new ideas safely.

## Rationale

- **Maintainability** – Production engineers can focus on the API and mining logic without navigating esoteric research code.  Researchers can experiment freely without worrying about breaking production.
- **Security and compliance** – Isolating research modules reduces the attack surface and simplifies dependency management.
- **Release management** – Production releases can be versioned independently from research prototypes.

## Proposed structure

1. **Create a new repository**, e.g., `hyba_research`, to host experimental algorithms, quantum simulations, and mathematical certificates.
2. **Move research modules** from `python_backend/pythia_mining` and `docs/scientific` into the new repository.  For example:
   - `pythia_mining/tensor_network_*.py`
   - `pythia_mining/iit_*.py`
   - `docs/scientific/*`
3. **Define stable interfaces** in the production code (e.g., an abstract base class `NonceSearchStrategy`) that production modules use to interact with research implementations.
4. **Use package versioning** – Publish the research repository as a versioned Python package that can be installed via pip.  Production dependencies can pin a specific version.
5. **Establish a contribution process** – New research features should be reviewed by both research and production maintainers before being integrated.  Integration should include tests and benchmark results.

## Migration steps

- [ ] Inventory existing research modules and create an issue tracker to move them.
- [ ] Set up CI/CD for the `hyba_research` repository, including tests and dependency scanning.
- [ ] Deprecate direct imports of research modules in the production code; replace them with calls to the abstract interface.
- [ ] Update documentation to reflect the new architecture.

Separating research from production is a non‑trivial effort but will pay dividends in maintainability and safety over the long term.
