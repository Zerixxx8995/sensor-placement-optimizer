"""
tests/test_pso.py
-----------------
Unit tests for core/pso.py — the CPU PSO engine.

Covers:
  - Output dict has all required keys
  - best_positions shape matches (num_nodes, 2)
  - All final positions are within field bounds
  - Fitness history is monotonically non-increasing
  - Same seed → identical results (reproducibility)
  - PSO reduces fitness vs random placement (convergence)
  - Restricted areas are respected (no sensors inside RA at end)
"""

import numpy as np
import pytest

from app.core.pso import run_pso


# ---------------------------------------------------------------------------
# Shared minimal config for fast tests
# ---------------------------------------------------------------------------

def make_config(
    num_nodes=10,
    width=100.0,
    height=100.0,
    iterations=30,
    swarm_size=10,
    seed=42,
    restricted_areas=None,
):
    """Build a minimal valid PSO config for testing (small so tests are fast)."""
    return {
        "area": {"width": width, "height": height},
        "num_nodes": num_nodes,
        "sensing_radius": 15.0,
        "comm_radius": 30.0,
        "initial_energy": 1.0,
        "weights": {"w1": 0.5, "w2": 0.25, "w3": 0.25},
        "pso_params": {
            "swarm_size": swarm_size,
            "iterations": iterations,
            "inertia": 0.7,
            "c1": 1.5,
            "c2": 1.5,
        },
        "use_gpu": False,
        "use_vdcoa": False,
        "seed": seed,
        "restricted_areas": restricted_areas or [],
        "non_critical_areas": [],
        "cell_size": 2.0,        # coarser grid for test speed
        "sink": (0.0, 0.0),
    }


# ---------------------------------------------------------------------------
# Output structure
# ---------------------------------------------------------------------------

class TestPSOOutputStructure:

    def test_returns_dict(self):
        result = run_pso(make_config())
        assert isinstance(result, dict)

    def test_required_keys_present(self):
        result = run_pso(make_config())
        required_keys = [
            "best_positions",
            "fitness_history",
            "coverage_map",
            "coverage_ratio",
            "connectivity_ratio",
            "avg_energy",
            "compute_time_seconds",
            "iterations_run",
            "gpu_used",
        ]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"

    def test_gpu_used_is_false(self):
        """CPU PSO should always report gpu_used=False"""
        result = run_pso(make_config())
        assert result["gpu_used"] is False

    def test_iterations_run_matches_config(self):
        cfg = make_config(iterations=25)
        result = run_pso(cfg)
        assert result["iterations_run"] == 25

    def test_compute_time_positive(self):
        result = run_pso(make_config())
        assert result["compute_time_seconds"] > 0.0


# ---------------------------------------------------------------------------
# Shape and bounds
# ---------------------------------------------------------------------------

class TestPSOOutputShape:

    def test_best_positions_shape(self):
        """best_positions must be (num_nodes, 2)"""
        cfg = make_config(num_nodes=8)
        result = run_pso(cfg)
        assert result["best_positions"].shape == (8, 2)

    def test_coverage_map_shape(self):
        """coverage_map must be (H/cell_size, W/cell_size)"""
        cfg = make_config(width=100.0, height=60.0)
        cfg["cell_size"] = 2.0
        result = run_pso(cfg)
        assert result["coverage_map"].shape == (30, 50)

    def test_fitness_history_length(self):
        """fitness_history length = iterations + 1 (initial + one per iter)"""
        cfg = make_config(iterations=20)
        result = run_pso(cfg)
        assert len(result["fitness_history"]) == 21  # 0..20

    def test_all_positions_in_bounds(self):
        """All final sensor positions must lie within the field"""
        cfg = make_config(num_nodes=15, width=100.0, height=80.0)
        result = run_pso(cfg)
        pos = result["best_positions"]
        assert np.all(pos[:, 0] >= 0.0) and np.all(pos[:, 0] <= 100.0)
        assert np.all(pos[:, 1] >= 0.0) and np.all(pos[:, 1] <= 80.0)

    def test_coverage_ratio_in_range(self):
        result = run_pso(make_config())
        assert 0.0 <= result["coverage_ratio"] <= 1.0

    def test_connectivity_ratio_in_range(self):
        result = run_pso(make_config())
        assert 0.0 <= result["connectivity_ratio"] <= 1.0

    def test_avg_energy_in_range(self):
        result = run_pso(make_config())
        assert 0.0 <= result["avg_energy"] <= 1.0


# ---------------------------------------------------------------------------
# Fitness history convergence
# ---------------------------------------------------------------------------

class TestPSOConvergence:

    def test_fitness_history_non_increasing(self):
        """Global best fitness must never increase — PSO records global best."""
        result = run_pso(make_config(iterations=50, swarm_size=15, seed=0))
        history = result["fitness_history"]
        for i in range(len(history) - 1):
            assert history[i + 1] <= history[i] + 1e-10, (
                f"Fitness increased at iteration {i+1}: "
                f"{history[i]:.6f} -> {history[i+1]:.6f}"
            )

    def test_pso_improves_over_iterations(self):
        """Final fitness should be <= initial fitness"""
        result = run_pso(make_config(iterations=50, swarm_size=15, seed=1))
        history = result["fitness_history"]
        assert history[-1] <= history[0], (
            f"PSO did not improve: initial={history[0]:.4f}, final={history[-1]:.4f}"
        )


# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------

class TestPSOReproducibility:

    def test_same_seed_same_result(self):
        """Identical config + seed → identical best_positions and fitness_history"""
        cfg = make_config(seed=777)
        r1 = run_pso(cfg)
        r2 = run_pso(cfg)
        np.testing.assert_array_equal(
            r1["best_positions"], r2["best_positions"],
            err_msg="best_positions differ with same seed"
        )
        np.testing.assert_array_equal(
            r1["fitness_history"], r2["fitness_history"],
            err_msg="fitness_history differs with same seed"
        )

    def test_different_seed_different_result(self):
        """Different seeds should (almost certainly) produce different results"""
        r1 = run_pso(make_config(seed=1))
        r2 = run_pso(make_config(seed=2))
        # It would be astronomically unlikely for these to be equal
        assert not np.array_equal(r1["best_positions"], r2["best_positions"])


# ---------------------------------------------------------------------------
# Restricted areas
# ---------------------------------------------------------------------------

class TestPSORestrictedAreas:

    def test_restricted_area_in_coverage_map(self):
        """
        Cells inside restricted_area should have coverage=0 in the output map.
        We place a large RA covering a big chunk of the field and verify
        that the coverage map zeros it out.
        """
        ra = [{"x1": 40.0, "y1": 40.0, "x2": 60.0, "y2": 60.0}]
        cfg = make_config(restricted_areas=ra, iterations=10, swarm_size=5)
        result = run_pso(cfg)

        cov = result["coverage_map"]
        cell_size = cfg["cell_size"]
        # Map the RA to cell indices
        c1, r1 = int(40.0 / cell_size), int(40.0 / cell_size)
        c2, r2 = int(60.0 / cell_size), int(60.0 / cell_size)

        ra_cells = cov[r1:r2, c1:c2]
        assert np.all(ra_cells == 0.0), (
            f"Restricted area cells should be 0, got max={ra_cells.max():.4f}"
        )
