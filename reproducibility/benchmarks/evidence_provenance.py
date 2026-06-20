#!/usr/bin/env python3
"""
Evidence Tagging and Provenance Tracking System for HYBA PQMC Benchmarks

This module provides cryptographic evidence tagging, provenance tracking,
and verification capabilities for all benchmark results, ensuring auditability
and reproducibility at enterprise grade.
"""

import hashlib
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import platform


@dataclass
class ProvenanceRecord:
    """Complete provenance record for benchmark results."""
    record_id: str
    timestamp: str
    benchmark_id: str
    dataset_provenance: Dict[str, Any]
    code_provenance: Dict[str, Any]
    environment_provenance: Dict[str, Any]
    execution_provenance: Dict[str, Any]
    result_provenance: Dict[str, Any]
    cryptographic_evidence: Dict[str, str]
    verification_status: str
    audit_trail: List[str]


class EvidenceProvenanceSystem:
    """Enterprise-grade evidence tagging and provenance tracking system."""
    
    def __init__(self, benchmark_id: str):
        self.benchmark_id = benchmark_id
        self.audit_trail = []
        self._log("Evidence provenance system initialized for benchmark", benchmark_id)
        
    def _log(self, message: str, *args):
        """Add entry to audit trail."""
        entry = f"{datetime.now(timezone.utc).isoformat()}: {message.format(*args)}"
        self.audit_trail.append(entry)
        
    def _sha256_hash(self, data: bytes) -> str:
        """Generate SHA-256 hash."""
        return hashlib.sha256(data).hexdigest()
    
    def _sha3_256_hash(self, data: bytes) -> str:
        """Generate SHA3-256 hash for additional security."""
        import hashlib
        return hashlib.sha3_256(data).hexdigest()
    
    def capture_dataset_provenance(self, dataset: Any, dataset_source: str) -> Dict[str, Any]:
        """Capture complete dataset provenance."""
        self._log("Capturing dataset provenance from", dataset_source)
        
        import numpy as np
        
        if isinstance(dataset, np.ndarray):
            dataset_hash = self._sha256_hash(dataset.tobytes())
            dataset_size = dataset.nbytes
            dataset_shape = dataset.shape
            dataset_dtype = str(dataset.dtype)
        else:
            dataset_hash = self._sha256_hash(json.dumps(dataset).encode())
            dataset_size = len(json.dumps(dataset))
            dataset_shape = "N/A"
            dataset_dtype = "N/A"
        
        provenance = {
            "source": dataset_source,
            "hash_sha256": dataset_hash,
            "hash_sha3_256": self._sha3_256_hash(dataset.tobytes() if isinstance(dataset, np.ndarray) else json.dumps(dataset).encode()),
            "size_bytes": dataset_size,
            "shape": dataset_shape,
            "dtype": dataset_dtype,
            "capture_timestamp": datetime.now(timezone.utc).isoformat(),
            "capture_method": "automatic",
            "data_classification": "public"  # Can be enhanced
        }
        
        self._log("Dataset provenance captured: hash={}, size={}", dataset_hash, dataset_size)
        return provenance
    
    def capture_code_provenance(self, code_path: str) -> Dict[str, Any]:
        """Capture complete code provenance."""
        self._log("Capturing code provenance from", code_path)
        
        code_path = Path(code_path)
        
        # Git information
        git_info = {}
        try:
            git_info = {
                "commit": subprocess.check_output(['git', 'rev-parse', 'HEAD'], 
                                                  cwd=code_path.parent.parent.parent,
                                                  stderr=subprocess.DEVNULL).decode().strip(),
                "branch": subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                                                  cwd=code_path.parent.parent.parent,
                                                  stderr=subprocess.DEVNULL).decode().strip(),
                "commit_timestamp": subprocess.check_output(['git', 'log', '-1', '--format=%ci'],
                                                              cwd=code_path.parent.parent.parent,
                                                              stderr=subprocess.DEVNULL).decode().strip(),
                "author": subprocess.check_output(['git', 'log', '-1', '--format=%an'],
                                                  cwd=code_path.parent.parent.parent,
                                                  stderr=subprocess.DEVNULL).decode().strip(),
                "message": subprocess.check_output(['git', 'log', '-1', '--format=%s'],
                                                  cwd=code_path.parent.parent.parent,
                                                  stderr=subprocess.DEVNULL).decode().strip()
            }
        except Exception as e:
            self._log("Git information capture failed: {}", str(e))
            git_info = {"error": str(e)}
        
        # File information
        if code_path.exists():
            with open(code_path, 'rb') as f:
                code_content = f.read()
            code_hash = self._sha256_hash(code_content)
            code_size = len(code_content)
            code_lines = len(code_content.decode('utf-8', errors='ignore').split('\n'))
        else:
            code_hash = "N/A"
            code_size = 0
            code_lines = 0
        
        provenance = {
            "file_path": str(code_path),
            "file_hash_sha256": code_hash,
            "file_hash_sha3_256": self._sha3_256_hash(code_content if code_path.exists() else b""),
            "file_size_bytes": code_size,
            "file_lines": code_lines,
            "git": git_info,
            "capture_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        self._log("Code provenance captured: hash={}, lines={}", code_hash, code_lines)
        return provenance
    
    def capture_environment_provenance(self) -> Dict[str, Any]:
        """Capture complete environment provenance."""
        self._log("Capturing environment provenance")
        
        # Python environment
        import sys
        import numpy as np
        
        python_info = {
            "version": sys.version,
            "executable": sys.executable,
            "implementation": sys.implementation.name if hasattr(sys, 'implementation') else "CPython"
        }
        
        # Package versions
        packages = {}
        try:
            import pip
            installed = subprocess.check_output([sys.executable, '-m', 'pip', 'list'], 
                                               stderr=subprocess.DEVNULL).decode()
            for line in installed.split('\n')[2:]:
                if line:
                    parts = line.split()
                    if len(parts) >= 2:
                        packages[parts[0]] = parts[1]
        except:
            pass
        
        # System information
        system_info = {
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "cpu_count": None
        }
        
        try:
            import os
            system_info["cpu_count"] = os.cpu_count()
        except:
            pass
        
        # Memory information
        memory_info = {}
        try:
            import psutil
            memory = psutil.virtual_memory()
            memory_info = {
                "total_gb": memory.total / (1024**3),
                "available_gb": memory.available / (1024**3),
                "percent_used": memory.percent
            }
        except:
            pass
        
        provenance = {
            "python": python_info,
            "numpy_version": np.__version__,
            "packages": packages,
            "system": system_info,
            "memory": memory_info,
            "capture_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        self._log("Environment provenance captured")
        return provenance
    
    def capture_execution_provenance(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Capture execution provenance."""
        self._log("Capturing execution provenance")
        
        import os
        
        provenance = {
            "parameters": parameters,
            "environment_variables": {
                k: v for k, v in os.environ.items() 
                if k.startswith(('HYBA_', 'PYTHON', 'PATH'))
            },
            "working_directory": os.getcwd(),
            "user": os.getlogin() if hasattr(os, 'getlogin') else "unknown",
            "pid": os.getpid(),
            "start_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        self._log("Execution provenance captured")
        return provenance
    
    def capture_result_provenance(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Capture result provenance."""
        self._log("Capturing result provenance")
        
        results_json = json.dumps(results, sort_keys=True)
        result_hash = self._sha256_hash(results_json.encode())
        result_size = len(results_json)
        
        provenance = {
            "result_hash_sha256": result_hash,
            "result_hash_sha3_256": self._sha3_256_hash(results_json.encode()),
            "result_size_bytes": result_size,
            "result_keys": list(results.keys()),
            "capture_timestamp": datetime.now(timezone.utc).isoformat(),
            "result_count": len(results) if isinstance(results, (list, dict)) else 1
        }
        
        self._log("Result provenance captured: hash={}, size={}", result_hash, result_size)
        return provenance
    
    def generate_cryptographic_evidence(self, all_provenance: Dict[str, Any]) -> Dict[str, str]:
        """Generate cryptographic evidence for all provenance."""
        self._log("Generating cryptographic evidence")
        
        # Combine all provenance into a single hash
        combined = json.dumps(all_provenance, sort_keys=True)
        
        evidence = {
            "combined_hash_sha256": self._sha256_hash(combined.encode()),
            "combined_hash_sha3_256": self._sha3_256_hash(combined.encode()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "evidence_version": "1.0",
            "hash_algorithm": "SHA-256 and SHA3-256"
        }
        
        # In production, add digital signature
        # evidence["digital_signature"] = self._sign(combined)
        
        self._log("Cryptographic evidence generated")
        return evidence
    
    def create_provenance_record(self, dataset: Any, dataset_source: str, code_path: str,
                                  parameters: Dict[str, Any], results: Dict[str, Any]) -> ProvenanceRecord:
        """Create complete provenance record."""
        self._log("Creating complete provenance record")
        
        record_id = f"prov-{self.benchmark_id}-{int(time.time())}"
        
        dataset_prov = self.capture_dataset_provenance(dataset, dataset_source)
        code_prov = self.capture_code_provenance(code_path)
        env_prov = self.capture_environment_provenance()
        exec_prov = self.capture_execution_provenance(parameters)
        result_prov = self.capture_result_provenance(results)
        
        all_provenance = {
            "dataset": dataset_prov,
            "code": code_prov,
            "environment": env_prov,
            "execution": exec_prov,
            "result": result_prov
        }
        
        crypto_evidence = self.generate_cryptographic_evidence(all_provenance)
        
        record = ProvenanceRecord(
            record_id=record_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            benchmark_id=self.benchmark_id,
            dataset_provenance=dataset_prov,
            code_provenance=code_prov,
            environment_provenance=env_prov,
            execution_provenance=exec_prov,
            result_provenance=result_prov,
            cryptographic_evidence=crypto_evidence,
            verification_status="pending",
            audit_trail=self.audit_trail.copy()
        )
        
        self._log("Provenance record created: {}", record_id)
        return record
    
    def verify_provenance(self, record: ProvenanceRecord) -> bool:
        """Verify provenance record integrity."""
        self._log("Verifying provenance record: {}", record.record_id)
        
        # Re-compute combined hash
        all_provenance = {
            "dataset": record.dataset_provenance,
            "code": record.code_provenance,
            "environment": record.environment_provenance,
            "execution": record.execution_provenance,
            "result": record.result_provenance
        }
        
        combined = json.dumps(all_provenance, sort_keys=True)
        computed_hash = self._sha256_hash(combined.encode())
        
        # Verify hash matches
        if computed_hash != record.cryptographic_evidence["combined_hash_sha256"]:
            self._log("Hash verification failed: expected={}, computed={}", 
                     record.cryptographic_evidence["combined_hash_sha256"], computed_hash)
            return False
        
        self._log("Provenance verification successful")
        return True
    
    def export_provenance(self, record: ProvenanceRecord, output_path: str):
        """Export provenance record to file."""
        self._log("Exporting provenance record to", output_path)
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(asdict(record), f, indent=2)
        
        self._log("Provenance record exported")
    
    def import_provenance(self, input_path: str) -> ProvenanceRecord:
        """Import provenance record from file."""
        self._log("Importing provenance record from", input_path)
        
        with open(input_path, 'r') as f:
            data = json.load(f)
        
        record = ProvenanceRecord(**data)
        self._log("Provenance record imported")
        return record


def main():
    """Test the evidence provenance system."""
    import numpy as np
    
    # Create test system
    system = EvidenceProvenanceSystem("test-benchmark")
    
    # Create test data
    test_data = np.random.randn(100, 100)
    test_params = {"seed": 42, "iterations": 100}
    test_results = {"accuracy": 0.95, "time": 1.23}
    
    # Create provenance record
    record = system.create_provenance_record(
        dataset=test_data,
        dataset_source="synthetic_test",
        code_path="/Users/demouser/Desktop/HYBA_FULLSTACK/reproducibility/benchmarks/enterprise_benchmark_suite.py",
        parameters=test_params,
        results=test_results
    )
    
    # Verify provenance
    verified = system.verify_provenance(record)
    print(f"Provenance verification: {verified}")
    
    # Export provenance
    system.export_provenance(record, "validation_output/test_provenance.json")
    print("Provenance record exported to validation_output/test_provenance.json")


if __name__ == "__main__":
    main()
