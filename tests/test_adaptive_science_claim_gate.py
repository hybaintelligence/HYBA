"""
Proof gate tests for the Controlled Adaptive Systems Science Program.

These tests are deliberately conservative. They verify that the measurement
instrument can detect a controlled feedback/update pattern and that the science
programme preserves the proof ladder before claims advance.
"""

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).parent.parent
ADAPTIVE_TEST_FILE = ROOT / "tests" / "test_adaptive_behavior_deep_analysis.py"

spec = importlib.util.spec_from_file_location("adaptive_behavior_deep_analysis", ADAPTIVE_TEST_FILE)
adaptive_module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(adaptive_module)

FeedbackLoopDetector = adaptive_module.FeedbackLoopDetector
MemoryAccumulationDetector = adaptive_module.MemoryAccumulationDetector
ParameterOptimizationDetector = adaptive_module.ParameterOptimizationDetector


def test_feedback_detector_catches_controlled_state_update(tmp_path):
    sample = tmp_path / "controlled_state_system.py"
    sample.write_text(
        """
class ControlledStateSystem:
    def __init__(self):
        self.score = 1.0
        self.history = []
        self.threshold = 0.5

    def update_score(self, measurement):
        self.score = self.score * 0.9 + measurement * 0.1
        self.history.append(self.score)
        if self.score > self.threshold:
            self.threshold += 0.05
        return self.score
""".strip(),
        encoding="utf-8",
    )

    result = FeedbackLoopDetector().analyze_python_file(sample)
    loop_types = {entry["type"] for entry in result["feedback_loops"]}

    assert result["count"] >= 2
    assert "state_feedback" in loop_types
    assert "update_method" in loop_types
    assert "accumulation" in loop_types


def test_memory_and_optimization_detectors_are_distinct(tmp_path):
    sample = tmp_path / "memory_and_threshold_system.py"
    sample.write_text(
        """
class MemoryAndThresholdSystem:
    def __init__(self):
        self.memory = []
        self.dynamic_config = {"threshold": 0.1}

    def record(self, item):
        self.memory.append(item)
        self.dynamic_config["threshold"] = self.dynamic_config["threshold"] + 0.01
""".strip(),
        encoding="utf-8",
    )

    memory = MemoryAccumulationDetector().analyze_file(sample)
    optimisation = ParameterOptimizationDetector().analyze_file(sample)

    assert memory["count"] > 0
    assert optimisation["count"] > 0


def test_controlled_science_program_preserves_proof_ladder():
    program = ROOT / "docs" / "CONTROLLED_ADAPTIVE_SYSTEMS_SCIENCE_PROGRAM.md"
    content = program.read_text(encoding="utf-8")

    assert "observe -> preserve -> instrument -> test -> replicate -> falsify" in content
    assert "compare baselines" in content
    assert "external review" in content
    assert "claim-boundary" in content


def test_adaptive_artifact_claim_boundary_when_present():
    artifact = ROOT / "artifacts" / "adaptive_behavior_analysis.json"
    if not artifact.exists():
        return

    data = json.loads(artifact.read_text(encoding="utf-8"))
    boundary = data.get("claim_boundary")

    assert boundary, "adaptive behavior artifact must carry claim-boundary metadata"
    assert "supported" in boundary
    assert "not_supported_by_this_test_alone" in boundary
