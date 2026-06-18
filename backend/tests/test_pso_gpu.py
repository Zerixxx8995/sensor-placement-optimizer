"""
tests/test_pso_gpu.py
---------------------
Unit tests for core/pso_gpu.py — GPU-accelerated PSO engine.

Test strategy
-------------
GPU-specific tests (marked @cuda_required) are skipped automatically if no
CUDA device is present. ALL other tests run unconditionally, covering:

  - is_gpu_available() returns a bool without error
  - run_pso_gpu() on any host (GPU or CPU fallback):
      * returns the required result dict structure
      * best_positions shape is (num_nodes, 2)
      * all positions are within field bounds
      * fitness_history is monotonically non-increasing
      * coverage/connectivity ratios in [0, 1]
      * iterations_run matches config
      * gpu_used flag matches reality
      * same seed → identical results (reproducibility)

GPU-only tests (skipped on CPU-only machines):
  - gpu_used is True
  - GPU fitness values match CPU within tolerance 1e-4
  - GPU coverage_ratio matches CPU within tolerance 1e-4
  - GPU convergence is monotonically non-increasing (same guarantee as CPU)
"""

from __future__ import annotations

import numpy as np
import pytest

from app.core.pso_gpu import run_pso_gpu, is_gpu_available
from app.core.pso import run_pso


# ---------------------------------------------------------------------------
# Markers
# ---------------------------------------------------------------------------

cuda_required = pytest.mark.skipif(
    not is_gpu_available(),
    reason="No CUDA-capable GPU detected — GPU kernel tests skipped",
)

cpu_fallback_only = pytest.mark.skipif(
    is_gpu_available(),
    reason="GPU is available — fallback-path tests not applicable",
)


# ---------------------------------------------------------------------------
# Shared minimal config (small so tests run fast on CPU too)
# ---------------------------------------------------------------------------

SMALL_CONFIG = {
    "area": {"width": 50.0, "height": 50.0},
    "num_nodes": 5,
    "sensing_radius": 8.0,
    "comm_radius": 16.0,
    "initial_energy": 1.0,
    "weights": {"w1": 0.5, "w2": 0.25, "w3": 0.25},
    "pso_params": {
        "swarm_size": 5,
        "iterations": 10,
        "inertia": 0.7,
        "c1": 1.5,
        "c2": 1.5,
    },
    "use_gpu": True,
    "seed": 42,
    "restricted_areas": [],
    "cell_size": 5.0,
    "sink": (0.0, 0.0),
}


# ---------------------------------------------------------------------------
# Detection utility
# ---------------------------------------------------------------------------

class TestGPUDetection:

    def test_is_gpu_available_returns_bool(self):
        """is_gpu_available() must return a bool without raising."""
        result = is_gpu_available()
        assert isinstance(result, bool)

    def test_detection_idempotent(self):
        """Multiple calls return the same value."""
        assert is_gpu_available() == is_gpu_available()


# ---------------------------------------------------------------------------
# Result structure (runs on ALL machines — GPU or CPU fallback)
# ---------------------------------------------------------------------------

class TestGPUResultStructure:

    def test_returns_dict(self):
        result = run_pso_gpu(SMALL_CONFIG)
        assert isinstance(result, dict)

    def test_required_keys_present(self):
        result = run_pso_gpu(SMALL_CONFIG)
        required = [
            "best_positions", "fitness_history", "coverage_map",
            "coverage_ratio", "connectivity_ratio", "avg_energy",
            "compute_time_seconds", "iterations_run", "gpu_used",
        ]
        for key in required:
            assert key in result, f"Missing key: {key}"

    def test_gpu_used_is_boolean(self):
        result = run_pso_gpu(SMALL_CONFIG)
        assert isinstance(result["gpu_used"], bool)

    def test_gpu_used_matches_availability(self):
        """gpu_used should be True iff a GPU was actually used."""
        result = run_pso_gpu(SMALL_CONFIG)
        assert result["gpu_used"] == is_gpu_available()

    def test_iterations_run_matches_config(self):
        result = run_pso_gpu(SMALL_CONFIG)
        assert result["iterations_run"] == SMALL_CONFIG["pso_params"]["iterations"]

    def test_compute_time_positive(self):
        result = run_pso_gpu(SMALL_CONFIG)
        assert result["compute_time_seconds"] > 0.0


# ---------------------------------------------------------------------------
# Shape and bounds (runs on ALL machines)
# ---------------------------------------------------------------------------

class TestGPUOutputShape:

    def test_best_positions_shape(self):
        result = run_pso_gpu(SMALL_CONFIG)
        assert result["best_positions"].shape == (SMALL_CONFIG["num_nodes"], 2)

    def test_best_positions_in_bounds(self):
        result = run_pso_gpu(SMALL_CONFIG)
        pos = result["best_positions"]
        W, H = SMALL_CONFIG["area"]["width"], SMALL_CONFIG["area"]["height"]
        assert np.all(pos[:, 0] >= 0.0) and np.all(pos[:, 0] <= W)
        assert np.all(pos[:, 1] >= 0.0) and np.all(pos[:, 1] <= H)

    def test_fitness_history_length(self):
        """Length = iterations + 1 (initial value + one per iteration)."""
        result = run_pso_gpu(SMALL_CONFIG)
        assert len(result["fitness_history"]) == SMALL_CONFIG["pso_params"]["iterations"] + 1

    def test_coverage_map_is_2d_array(self):
        result = run_pso_gpu(SMALL_CONFIG)
        cmap = result["coverage_map"]
        assert isinstance(cmap, np.ndarray)
        assert cmap.ndim == 2

    def test_coverage_ratio_in_range(self):
        result = run_pso_gpu(SMALL_CONFIG)
        assert 0.0 <= result["coverage_ratio"] <= 1.0

    def test_connectivity_ratio_in_range(self):
        result = run_pso_gpu(SMALL_CONFIG)
        assert 0.0 <= result["connectivity_ratio"] <= 1.0

    def test_avg_energy_in_range(self):
        result = run_pso_gpu(SMALL_CONFIG)
        assert 0.0 <= result["avg_energy"] <= 1.0


# ---------------------------------------------------------------------------
# Convergence (runs on ALL machines)
# ---------------------------------------------------------------------------

class TestGPUConvergence:

    def test_fitness_history_non_increasing(self):
        """Global best must never worsen — the same guarantee as CPU PSO."""
        result = run_pso_gpu(SMALL_CONFIG)
        history = result["fitness_history"]
        for i in range(len(history) - 1):
            assert history[i + 1] <= history[i] + 1e-10, (
                f"Fitness increased at iter {i + 1}: "
                f"{history[i]:.6f} -> {history[i + 1]:.6f}"
            )

    def test_fitness_improves_or_stays(self):
        """Final fitness <= initial fitness."""
        result = run_pso_gpu(SMALL_CONFIG)
        history = result["fitness_history"]
        assert history[-1] <= history[0]


# ---------------------------------------------------------------------------
# Reproducibility (runs on ALL machines)
# ---------------------------------------------------------------------------

class TestGPUReproducibility:

    def test_same_seed_same_result(self):
        """Same config + seed → identical best_positions and fitness_history."""
        r1 = run_pso_gpu(SMALL_CONFIG)
        r2 = run_pso_gpu(SMALL_CONFIG)
        np.testing.assert_array_equal(
            r1["best_positions"], r2["best_positions"],
            err_msg="GPU best_positions differ with same seed"
        )
        np.testing.assert_array_equal(
            r1["fitness_history"], r2["fitness_history"],
            err_msg="GPU fitness_history differs with same seed"
        )

    def test_different_seeds_different_results(self):
        cfg_a = {**SMALL_CONFIG, "seed": 1}
        cfg_b = {**SMALL_CONFIG, "seed": 2}
        r1 = run_pso_gpu(cfg_a)
        r2 = run_pso_gpu(cfg_b)
        assert not np.array_equal(r1["best_positions"], r2["best_positions"])


# ---------------------------------------------------------------------------
# CPU fallback path
# ---------------------------------------------------------------------------

class TestCPUFallback:

    def test_fallback_sets_gpu_used_false(self):
        """On CPU-fallback, gpu_used must be False regardless of config."""
        result = run_pso_gpu(SMALL_CONFIG)
        if not is_gpu_available():
            assert result["gpu_used"] is False

    def test_fallback_result_identical_to_run_pso(self):
        """
        CPU fallback should produce the same result as run_pso() with the
        same seed, because it delegates directly to it.
        """
        if is_gpu_available():
            pytest.skip("GPU available — fallback delegation not triggered")

        gpu_result = run_pso_gpu(SMALL_CONFIG)
        cpu_result = run_pso(SMALL_CONFIG)

        np.testing.assert_array_almost_equal(
            gpu_result["best_positions"],
            cpu_result["best_positions"],
            decimal=10,
            err_msg="Fallback result should be identical to run_pso()",
        )


# ---------------------------------------------------------------------------
# GPU-specific tests (skipped on CPU-only machines)
# ---------------------------------------------------------------------------

class TestGPUKernelAccuracy:

    @cuda_required
    def test_gpu_used_is_true(self):
        """When CUDA is available, gpu_used must be True."""
        result = run_pso_gpu(SMALL_CONFIG)
        assert result["gpu_used"] is True

    @cuda_required
    def test_gpu_coverage_ratio_close_to_cpu(self):
        """
        GPU coverage_ratio must match CPU within 1e-4.
        Same seed → same positions → same coverage computation.
        """
        cpu = run_pso(SMALL_CONFIG)
        gpu = run_pso_gpu(SMALL_CONFIG)
        assert abs(gpu["coverage_ratio"] - cpu["coverage_ratio"]) < 1e-4, (
            f"GPU coverage={gpu['coverage_ratio']:.6f} differs from "
            f"CPU coverage={cpu['coverage_ratio']:.6f} by "
            f"{abs(gpu['coverage_ratio'] - cpu['coverage_ratio']):.2e}"
        )

    @cuda_required
    def test_gpu_best_positions_close_to_cpu(self):
        """
        GPU best_positions must be within tolerance of CPU.
        PSO positions update on CPU identically — only fitness differs.
        """
        cpu = run_pso(SMALL_CONFIG)
        gpu = run_pso_gpu(SMALL_CONFIG)
        np.testing.assert_allclose(
            gpu["best_positions"], cpu["best_positions"],
            rtol=1e-4, atol=1e-4,
            err_msg="GPU best_positions deviate too much from CPU",
        )

    @cuda_required
    def test_gpu_final_fitness_close_to_cpu(self):
        """Final fitness values should agree within 1e-4."""
        cpu = run_pso(SMALL_CONFIG)
        gpu = run_pso_gpu(SMALL_CONFIG)
        cpu_final = cpu["fitness_history"][-1]
        gpu_final = gpu["fitness_history"][-1]
        assert abs(gpu_final - cpu_final) < 1e-4, (
            f"GPU final fitness={gpu_final:.6f}, CPU={cpu_final:.6f}, "
            f"delta={abs(gpu_final - cpu_final):.2e}"
        )
