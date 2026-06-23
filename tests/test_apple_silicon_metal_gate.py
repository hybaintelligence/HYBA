from __future__ import annotations

import importlib
import sys
import types
from contextlib import contextmanager

import numpy as np


def _install_fake_mlx(monkeypatch):
    mlx_pkg = types.ModuleType("mlx")
    core = types.ModuleType("mlx.core")

    class FakeArray:
        def __init__(self, value):
            self.value = np.asarray(value, dtype=np.float32)

        def reshape(self, shape):
            return FakeArray(self.value.reshape(shape))

        def item(self):
            return float(np.asarray(self.value).item())

    @contextmanager
    def default_device(device):
        yield device

    core.float32 = np.float32
    core.gpu = object()
    core.cpu = object()
    core.default_device = default_device
    core.array = lambda value, dtype=None: FakeArray(np.asarray(value, dtype=dtype))
    core.matmul = lambda lhs, rhs: FakeArray(np.matmul(lhs.value, rhs.value))
    core.sum = lambda value: FakeArray(np.sum(value.value))
    core.eval = lambda value: None

    monkeypatch.setitem(sys.modules, "mlx", mlx_pkg)
    monkeypatch.setitem(sys.modules, "mlx.core", core)


def test_probe_reports_unavailable_without_apple_silicon(monkeypatch):
    module = importlib.import_module("pythia_mining.apple_silicon_metal")
    monkeypatch.setattr(module.platform, "system", lambda: "Linux")
    monkeypatch.setattr(module.platform, "machine", lambda: "x86_64")

    packet = module.probe_mlx_metal(matrix_size=8)

    assert packet["status"] == "unavailable"
    assert packet["apple_silicon_detected"] is False
    assert packet["metal_path_verified"] is False
    assert packet["forensic_sha256"]


def test_probe_verifies_fake_mlx_gpu_cpu_paths(monkeypatch):
    module = importlib.import_module("pythia_mining.apple_silicon_metal")
    monkeypatch.setattr(module.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(module.platform, "machine", lambda: "arm64")
    _install_fake_mlx(monkeypatch)

    packet = module.probe_mlx_metal(matrix_size=8, require_mlx=True)

    assert packet["status"] == "verified"
    assert packet["apple_silicon_detected"] is True
    assert packet["mlx_available"] is True
    assert packet["metal_path_verified"] is True
    assert packet["cpu_fallback_verified"] is True
    assert packet["absolute_delta"] < 1e-2
    assert (
        packet["unified_memory_semantics"]
        == "mlx_shared_memory_cpu_gpu_execution_measured"
    )
    assert packet["forensic_sha256"]


def test_probe_is_replay_stable_except_timing(monkeypatch):
    module = importlib.import_module("pythia_mining.apple_silicon_metal")
    monkeypatch.setattr(module.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(module.platform, "machine", lambda: "arm64")
    _install_fake_mlx(monkeypatch)

    first = module.probe_mlx_metal(matrix_size=8)
    second = module.probe_mlx_metal(matrix_size=8)

    for key in ("elapsed_ms", "forensic_sha256"):
        first.pop(key, None)
        second.pop(key, None)
    assert first == second
