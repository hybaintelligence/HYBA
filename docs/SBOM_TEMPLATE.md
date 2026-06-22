# Software Bill of Materials (SBOM)

## Overview

This document provides the Software Bill of Materials (SBOM) for the Salamander Regeneration Framework in multiple formats (SPDX, CycloneDX) to support supply chain security requirements from UK Government, US Government, and enterprise customers.

## SBOM Formats

### 1. SPDX 2.3 Format

**File**: `sbom.spdx.json`

```json
{
  "spdxVersion": "SPDX-2.3",
  "dataLicense": "CC0-1.0",
  "SPDXID": "SPDXRef-DOCUMENT",
  "name": "Salamander Regeneration Framework",
  "documentNamespace": "https://yourorg.com/salamander/1.0.0/sbom",
  "creationInfo": {
    "created": "2026-06-22T12:33:20Z",
    "creators": ["Tool: salamander-sbom-generator-1.0.0"],
    "licenseListVersion": "3.9"
  },
  "packages": [
    {
      "SPDXID": "SPDXRef-Package-Salamander",
      "name": "Salamander Regeneration Framework",
      "downloadLocation": "https://github.com/yourorg/salamander",
      "filesAnalyzed": true,
      "verificationCode": {
        "packageVerificationCodeValue": "d6a770ba38583ed4bb4525bd96e50461655d2758",
        "packageVerificationCodeExcludedFiles": []
      },
      "licenseConcluded": "MIT",
      "licenseDeclared": "MIT",
      "copyrightText": "Copyright 2026 Your Organization",
      "version": "1.0.0",
      "supplier": "Organization: Your Organization (contact@yourorg.com)",
      "externalRefs": [
        {
          "referenceCategory": "PACKAGE-MANAGER",
          "referenceType": "purl",
          "referenceLocator": "pkg:pypi/salamander-regeneration@1.0.0"
        }
      ]
    }
  ],
  "dependencies": [
    {
      "spdxElementRef": "SPDXRef-Package-Salamander",
      "dependency": [
        "SPDXRef-Package-numpy",
        "SPDXRef-Package-fastapi",
        "SPDXRef-Package-pydantic",
        "SPDXRef-Package-hypothesis"
      ]
    }
  ],
  "files": [
    {
      "SPDXID": "SPDXRef-File-stateful_regeneration.py",
      "fileName": "python_backend/pythia_mining/stateful_regeneration.py",
      "checksums": [
        {
          "algorithm": "SHA256",
          "checksumValue": "abc123..."
        }
      ],
      "licenseConcluded": "MIT",
      "copyrightText": "Copyright 2026 Your Organization"
    }
  ]
}
```

### 2. CycloneDX 1.4 Format

**File**: `sbom.cyclonedx.json`

```json
{
  "bomFormat": "CycloneDX",
  "specVersion": "1.4",
  "version": 1,
  "metadata": {
    "timestamp": "2026-06-22T12:33:20Z",
    "tools": [
      {
        "vendor": "Your Organization",
        "name": "salamander-sbom-generator",
        "version": "1.0.0"
      }
    ],
    "component": {
      "type": "application",
      "name": "Salamander Regeneration Framework",
      "version": "1.0.0",
      "description": "Quantum-inspired autonomous system self-healing",
      "licenses": [
        {
          "license": {
            "id": "MIT",
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT"
          }
        }
      ],
      "purl": "pkg:pypi/salamander-regeneration@1.0.0",
      "externalReferences": [
        {
          "type": "vcs",
          "url": "https://github.com/yourorg/salamander"
        }
      ]
    }
  },
  "components": [
    {
      "type": "library",
      "name": "numpy",
      "version": "1.24.3",
      "purl": "pkg:pypi/numpy@1.24.3",
      "licenses": [
        {
          "license": {
            "id": "BSD-3-Clause",
            "name": "BSD 3-Clause License"
          }
        }
      ]
    },
    {
      "type": "library",
      "name": "fastapi",
      "version": "0.100.0",
      "purl": "pkg:pypi/fastapi@0.100.0",
      "licenses": [
        {
          "license": {
            "id": "MIT",
            "name": "MIT License"
          }
        }
      ]
    },
    {
      "type": "library",
      "name": "pydantic",
      "version": "2.0.0",
      "purl": "pkg:pypi/pydantic@2.0.0",
      "licenses": [
        {
          "license": {
            "id": "MIT",
            "name": "MIT License"
          }
        }
      ]
    },
    {
      "type": "library",
      "name": "hypothesis",
      "version": "6.141.1",
      "purl": "pkg:pypi/hypothesis@6.141.1",
      "licenses": [
        {
          "license": {
            "id": "MPL-2.0",
            "name": "Mozilla Public License 2.0"
          }
        }
      ]
    }
  ],
  "dependencies": [
    {
      "ref": "pkg:pypi/salamander-regeneration@1.0.0",
      "dependsOn": [
        "pkg:pypi/numpy@1.24.3",
        "pkg:pypi/fastapi@0.100.0",
        "pkg:pypi/pydantic@2.0.0",
        "pkg:pypi/hypothesis@6.141.1"
      ]
    }
  ]
}
```

## SBOM Generation

### Automated Generation Script

```python
#!/usr/bin/env python3
"""
generate_sbom.py - Generate SBOM in SPDX and CycloneDX formats
"""

import json
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path

class SBOMGenerator:
    def __init__(self, project_name="Salamander Regeneration Framework", version="1.0.0"):
        self.project_name = project_name
        self.version = version
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        self.dependencies = self._get_dependencies()
    
    def _get_dependencies(self):
        """Extract dependencies from requirements.txt"""
        deps = []
        with open("requirements.txt") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("-r"):
                    # Parse package==version or package>=version
                    if "==" in line:
                        name, version = line.split("==")
                        deps.append({"name": name.strip(), "version": version.strip()})
                    elif ">=" in line:
                        name, version = line.split(">=")
                        deps.append({"name": name.strip(), "version": version.strip()})
        return deps
    
    def _calculate_file_hash(self, filepath):
        """Calculate SHA256 hash of file"""
        with open(filepath, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    
    def generate_spdx(self, output_file="sbom.spdx.json"):
        """Generate SPDX 2.3 SBOM"""
        sbom = {
            "spdxVersion": "SPDX-2.3",
            "dataLicense": "CC0-1.0",
            "SPDXID": "SPDXRef-DOCUMENT",
            "name": self.project_name,
            "documentNamespace": f"https://yourorg.com/salamander/{self.version}/sbom",
            "creationInfo": {
                "created": self.timestamp,
                "creators": ["Tool: salamander-sbom-generator-1.0.0"],
                "licenseListVersion": "3.9"
            },
            "packages": [
                {
                    "SPDXID": "SPDXRef-Package-Salamander",
                    "name": self.project_name,
                    "downloadLocation": "https://github.com/yourorg/salamander",
                    "filesAnalyzed": True,
                    "licenseConcluded": "MIT",
                    "licenseDeclared": "MIT",
                    "copyrightText": "Copyright 2026 Your Organization",
                    "version": self.version,
                    "supplier": "Organization: Your Organization (contact@yourorg.com)"
                }
            ],
            "dependencies": [
                {
                    "spdxElementRef": "SPDXRef-Package-Salamander",
                    "dependency": [f"SPDXRef-Package-{d['name']}" for d in self.dependencies]
                }
            ]
        }
        
        with open(output_file, "w") as f:
            json.dump(sbom, f, indent=2)
        
        print(f"SPDX SBOM generated: {output_file}")
        return output_file
    
    def generate_cyclonedx(self, output_file="sbom.cyclonedx.json"):
        """Generate CycloneDX 1.4 SBOM"""
        sbom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.4",
            "version": 1,
            "metadata": {
                "timestamp": self.timestamp,
                "component": {
                    "type": "application",
                    "name": self.project_name,
                    "version": self.version,
                    "licenses": [
                        {
                            "license": {
                                "id": "MIT",
                                "name": "MIT License"
                            }
                        }
                    ]
                }
            },
            "components": [
                {
                    "type": "library",
                    "name": d["name"],
                    "version": d["version"],
                    "purl": f"pkg:pypi/{d['name']}@{d['version']}"
                }
                for d in self.dependencies
            ]
        }
        
        with open(output_file, "w") as f:
            json.dump(sbom, f, indent=2)
        
        print(f"CycloneDX SBOM generated: {output_file}")
        return output_file

if __name__ == "__main__":
    generator = SBOMGenerator()
    generator.generate_spdx()
    generator.generate_cyclonedx()
```

## Supply Chain Security

### Provenance Tracking

**Tool**: SLSA (Supply-chain Levels for Software Artifacts)

```yaml
# .github/workflows/slsa.yml
name: SLSA Provenance

on:
  release:
    types: [published]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Build package
        run: python setup.py sdist bdist_wheel
      - name: Generate SBOM
        run: python generate_sbom.py
      - name: Sign artifacts
        run: |
          gpg --detach-sign --armor dist/salamander-1.0.0.tar.gz
          gpg --detach-sign --armor sbom.spdx.json
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: release-artifacts
          path: |
            dist/
            sbom.spdx.json
            sbom.spdx.json.asc
```

### Reproducible Builds

**Goal**: Ensure anyone can reproduce the exact same build from source

```bash
# Build script with reproducibility guarantees
#!/bin/bash
set -euo pipefail

# Pin all versions
PYTHON_VERSION=3.9.6
PIP_VERSION=21.2.4
SETUPTOOLS_VERSION=65.5.0

# Use specific Python version
pyenv install ${PYTHON_VERSION}
pyenv local ${PYTHON_VERSION}

# Pin pip
python -m pip install --upgrade pip==${PIP_VERSION}

# Install exact dependencies
pip install -r requirements.lock.txt

# Build with deterministic settings
export PYTHONHASHSEED=0
python setup.py sdist bdist_wheel

# Verify reproducibility
./verify_build.sh dist/salamander-1.0.0.tar.gz
```

### Dependency Scanning

**Tools**:
- **Snyk**: Vulnerability scanning
- **Dependabot**: Automated dependency updates
- **Safety**: Python-specific vulnerability scanner
- **OSV-Scanner**: Open Source Vulnerabilities scanner

**CI/CD Integration**:
```yaml
# .github/workflows/dependency_scan.yml
name: Dependency Scan

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * 1'  # Weekly on Monday

jobs:
  snyk:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Snyk scan
        uses: snyk/actions/python@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --severity-threshold=high
  
  safety:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Safety check
        run: |
          pip install safety
          safety check --json --output safety-report.json
```

## SBOM Distribution

### Channels

1. **GitHub Releases**: Attach SBOM to every release
2. **Package Registry**: Include SBOM in PyPI package metadata
3. **Documentation**: Publish on docs.salamander.yourorg.com
4. **API Endpoint**: Serve via `/api/sbom` endpoint

### API Endpoint

```python
@router.get("/api/sbom", response_model=Dict[str, Any])
async def get_sbom(format: str = "spdx"):
    """Get Software Bill of Materials"""
    if format == "spdx":
        return generate_spdx_sbom()
    elif format == "cyclonedx":
        return generate_cyclonedx_sbom()
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Use 'spdx' or 'cyclonedx'")
```

## Compliance Mapping

### Executive Order 14028 (US)

- **Requirement**: SBOM for all software purchased by US government
- **Salamander Compliance**: ✅ SPDX and CycloneDX formats provided
- **Distribution**: GitHub releases, PyPI, API endpoint

### UK Government Supply Chain Security

- **Requirement**: Supply chain risk management for critical infrastructure
- **Salamander Compliance**: ✅ Provenance tracking, reproducible builds, dependency scanning
- **Distribution**: NCSC-compliant SBOM format

### ISO/IEC 5972 (SBOM Standard)

- **Requirement**: Standardized SBOM formats
- **Salamander Compliance**: ✅ SPDX 2.3 and CycloneDX 1.4
- **Distribution**: Multiple formats for interoperability

## Verification

### SBOM Validation

```bash
# Validate SPDX SBOM
pip install spdx-tools
spdx-tools validate sbom.spdx.json

# Validate CycloneDX SBOM
pip install cyclonedx-bom
cyclonedx-bom validate sbom.cyclonedx.json
```

### Checksum Verification

```bash
# Verify artifact checksums
sha256sum -c checksums.txt

# Verify signatures
gpg --verify sbom.spdx.json.asc sbom.spdx.json
```

## Maintenance

### Update Schedule

- **Release SBOM**: With every release
- **Dependency Scan**: Weekly automated scan
- **SBOM Regeneration**: On dependency updates
- **Audit**: Quarterly SBOM audit

### Responsibilities

- **Release Manager**: Generate and publish SBOM with each release
- **Security Team**: Review SBOM for vulnerabilities
- **Compliance Officer**: Ensure regulatory compliance
- **Engineering**: Update dependencies and regenerate SBOM

## References

- [NTIA SBOM Minimum Elements](https://www.ntia.gov/page/sbom-minimum-elements)
- [SPDX Specification](https://spdx.github.io/spdx-spec/)
- [CycloneDX Specification](https://cyclonedx.org/specification/overview/)
- [SLSA Framework](https://slsa.dev/)
- [Executive Order 14028](https://www.whitehouse.gov/briefing-room/presidential-actions/2021/05/12/executive-order-on-improving-the-nations-cybersecurity/)

---

**Last Updated**: 2026-06-22  
**Owner**: Security/Compliance Team  
**Next Review**: 2026-07-22