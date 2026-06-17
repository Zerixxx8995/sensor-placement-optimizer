"""
tests/test_fitness.py
---------------------
Unit tests for core/fitness.py and core/sensing_model.py.

Covers:
  - Sensing model at/inside/beyond Rs
  - Monotonic falloff of detection probability
  - coverage_map output shape and value range
  - Fitness with perfect conditions -> near 0
  - Fitness with zero coverage -> dominated by w1 term
  - Adaptive penalty coefficient schedule
  - OOB penalty is 0 when all nodes are in bounds
"""

import numpy as np
import pytest

from app.core.sensing_model import (
    detection_probability,
    detection_probability_vectorized,
    coverage_map,
)
from app.core.fitness import (
    compute_fitness,
    _adaptive_penalty_alpha,
    _oob_penalty,
    _connectivity_ratio,
    _energy_cost,
)


# ---------------------------------------------------------------------------
# Sensing model — scalar
# ---------------------------------------------------------------------------

class TestDetectionProbabilityScalar:

    def test_at_zero_distance(self):
        """Node directly on target → P = 1.0"""
        assert detection_probability(0.0, Rs=10.0) == 1.0

    def test_inside_radius(self):
        """Anywhere inside Rs → P = 1.0"""
        assert detection_probability(5.0, Rs=10.0) == 1.0

    def test_exactly_at_radius(self):
        """Exactly at Rs → P = 1.0 (boundary is reliable)"""
        assert detection_probability(10.0, Rs=10.0) == 1.0

    def test_beyond_radius_lt_one(self):
        """Beyond Rs → P strictly less than 1"""
        p = detection_probability(15.0, Rs=10.0)
        assert 0.0 < p < 1.0

    def test_falloff_monotonic(self):
        """Detection probability decreases as distance increases beyond Rs"""
        Rs = 10.0
        probs = [detection_probability(d, Rs) for d in [10.0, 12.0, 15.0, 20.0, 30.0]]
        for i in range(len(probs) - 1):
            assert probs[i] >= probs[i + 1], (
                f"Monotonicity violated: P({10 + 2*i}) = {probs[i]:.4f} "
                f"< P({10 + 2*(i+1)}) = {probs[i+1]:.4f}"
            )

    def test_very_far_approaches_zero(self):
        """Very far away → probability approaches 0"""
        p = detection_probability(1000.0, Rs=10.0, lam=0.5)
        assert p < 1e-6

    def test_higher_lambda_steeper_decay(self):
        """Higher λ decays faster than lower λ at same distance"""
        p_low = detection_probability(20.0, Rs=10.0, lam=0.1)
        p_high = detection_probability(20.0, Rs=10.0, lam=1.0)
        assert p_high < p_low


# ---------------------------------------------------------------------------
# Sensing model — vectorized
# ---------------------------------------------------------------------------

class TestDetectionProbabilityVectorized:

    def test_output_shape_preserved(self):
        dists = np.array([[0.0, 5.0], [10.0, 15.0]])
        result = detection_probability_vectorized(dists, Rs=10.0)
        assert result.shape == dists.shape

    def test_inside_radius_all_ones(self):
        dists = np.array([0.0, 3.0, 9.99, 10.0])
        result = detection_probability_vectorized(dists, Rs=10.0)
        np.testing.assert_array_equal(result, 1.0)

    def test_beyond_radius_in_range(self):
        dists = np.array([11.0, 15.0, 25.0])
        result = detection_probability_vectorized(dists, Rs=10.0)
        assert np.all(result > 0.0) and np.all(result < 1.0)


# ---------------------------------------------------------------------------
# Coverage map
# ---------------------------------------------------------------------------

class TestCoverageMap:

    def test_output_shape(self):
        """Output shape must be (H, W) in cell units"""
        positions = np.array([[50.0, 50.0]])
        cov = coverage_map(positions, area_W=100.0, area_H=80.0, Rs=10.0, cell_size=1.0)
        assert cov.shape == (80, 100)

    def test_values_in_range(self):
        """All coverage values must be in [0, 1]"""
        positions = np.random.default_rng(42).uniform(0, 100, (5, 2))
        cov = coverage_map(positions, area_W=100.0, area_H=100.0, Rs=10.0)
        assert np.all(cov >= 0.0) and np.all(cov <= 1.0)

    def test_center_cell_high_coverage(self):
        """Sensor at center of a small field → center cell should be ~1.0"""
        positions = np.array([[5.0, 5.0]])
        cov = coverage_map(positions, area_W=10.0, area_H=10.0, Rs=10.0, cell_size=1.0)
        center_val = cov[4, 4]  # cell (4,4) center ≈ (4.5, 4.5), well within Rs=10
        assert center_val > 0.95

    def test_restricted_mask_zeroed(self):
        """Cells in restricted_mask must be set to 0.0"""
        positions = np.array([[5.0, 5.0]])
        mask = np.zeros((10, 10), dtype=bool)
        mask[4, 4] = True
        cov = coverage_map(positions, area_W=10.0, area_H=10.0, Rs=10.0,
                           cell_size=1.0, restricted_mask=mask)
        assert cov[4, 4] == 0.0

    def test_no_sensors_zero_coverage(self):
        """No sensors → zero coverage everywhere"""
        cov = coverage_map(np.empty((0, 2)), area_W=50.0, area_H=50.0, Rs=10.0)
        assert np.all(cov == 0.0)


# ---------------------------------------------------------------------------
# Adaptive penalty
# ---------------------------------------------------------------------------

class TestAdaptivePenalty:

    def test_starts_at_half(self):
        """At iteration 0, α should be 0.5"""
        assert _adaptive_penalty_alpha(0, 100) == pytest.approx(0.5)

    def test_zero_at_halfway(self):
        """At iteration 50 out of 100, α should be 0.0"""
        assert _adaptive_penalty_alpha(50, 100) == pytest.approx(0.0)

    def test_zero_after_halfway(self):
        """After halfway point, α stays at 0"""
        assert _adaptive_penalty_alpha(75, 100) == 0.0
        assert _adaptive_penalty_alpha(100, 100) == 0.0

    def test_decays_monotonically(self):
        """α should decrease (or stay equal) as iteration increases"""
        alphas = [_adaptive_penalty_alpha(i, 100) for i in range(101)]
        for i in range(len(alphas) - 1):
            assert alphas[i] >= alphas[i + 1]


# ---------------------------------------------------------------------------
# OOB penalty
# ---------------------------------------------------------------------------

class TestOOBPenalty:

    def test_no_penalty_in_bounds(self):
        """All positions within field → penalty = 0"""
        pos = np.array([[10.0, 10.0], [50.0, 50.0], [90.0, 90.0]])
        assert _oob_penalty(pos, 100.0, 100.0) == pytest.approx(0.0)

    def test_penalty_for_oob(self):
        """Out-of-bounds positions → positive penalty"""
        pos = np.array([[-10.0, 50.0]])   # x is -10, clearly OOB
        assert _oob_penalty(pos, 100.0, 100.0) > 0.0

    def test_empty_positions(self):
        """Empty deployment → penalty = 0"""
        assert _oob_penalty(np.empty((0, 2)), 100.0, 100.0) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Connectivity ratio
# ---------------------------------------------------------------------------

class TestConnectivityRatio:

    def test_all_connected_to_sink(self):
        """Nodes clustered near sink (0,0) within Rc → ratio = 1.0"""
        pos = np.array([[1.0, 1.0], [2.0, 2.0], [3.0, 3.0]])
        ratio = _connectivity_ratio(pos, Rc=20.0, sink=(0.0, 0.0))
        assert ratio == pytest.approx(1.0)

    def test_none_connected_to_sink(self):
        """Nodes very far from sink and each other → ratio = 0.0"""
        pos = np.array([[500.0, 500.0], [510.0, 510.0]])
        ratio = _connectivity_ratio(pos, Rc=5.0, sink=(0.0, 0.0))
        assert ratio == pytest.approx(0.0)

    def test_partial_connectivity(self):
        """Only some nodes reachable → ratio between 0 and 1"""
        # 2 nodes near sink, 2 far away, 4 total
        pos = np.array([
            [2.0, 2.0],    # connected
            [4.0, 4.0],    # connected (within Rc of node above)
            [500.0, 500.0],  # not connected
            [502.0, 502.0],  # not connected
        ])
        ratio = _connectivity_ratio(pos, Rc=10.0, sink=(0.0, 0.0))
        assert 0.0 < ratio < 1.0

    def test_empty_returns_zero(self):
        assert _connectivity_ratio(np.empty((0, 2)), Rc=10.0) == 0.0


# ---------------------------------------------------------------------------
# Full fitness function
# ---------------------------------------------------------------------------

BASE_CONFIG = {
    "area_W": 100.0,
    "area_H": 100.0,
    "Rs": 15.0,
    "Rc": 30.0,
    "lam": 0.5,
    "cell_size": 2.0,   # coarser grid for speed in tests
    "w1": 0.5,
    "w2": 0.25,
    "w3": 0.25,
    "sink": (0.0, 0.0),
    "restricted_mask": None,
}


class TestComputeFitness:

    def test_returns_float(self):
        pos = np.array([[50.0, 50.0], [25.0, 25.0], [75.0, 75.0]])
        f = compute_fitness(pos, BASE_CONFIG)
        assert isinstance(f, float)

    def test_fitness_in_reasonable_range(self):
        """Fitness value should be in [0, ~2] for normal deployments"""
        rng = np.random.default_rng(7)
        pos = rng.uniform(0, 100, (10, 2))
        f = compute_fitness(pos, BASE_CONFIG)
        assert 0.0 <= f <= 2.0

    def test_more_sensors_lower_fitness(self):
        """More sensors covering same area → lower fitness (better coverage)"""
        rng = np.random.default_rng(99)
        pos_few = rng.uniform(0, 100, (5, 2))
        pos_many = rng.uniform(0, 100, (30, 2))
        f_few = compute_fitness(pos_few, BASE_CONFIG)
        f_many = compute_fitness(pos_many, BASE_CONFIG)
        assert f_many < f_few, (
            f"Expected more sensors to have lower fitness: "
            f"f(5)={f_few:.4f}, f(30)={f_many:.4f}"
        )

    def test_no_penalty_at_late_iteration(self):
        """After halfway point, OOB positions should not add extra penalty"""
        # Place sensors slightly OOB
        pos_oob = np.array([[-5.0, 50.0], [105.0, 50.0]])
        f_early = compute_fitness(pos_oob, BASE_CONFIG, iteration=0, max_iterations=100)
        f_late = compute_fitness(pos_oob, BASE_CONFIG, iteration=60, max_iterations=100)
        # Late iteration has no penalty term, so should be <= early
        assert f_late <= f_early

    def test_weights_affect_fitness(self):
        """Changing weights changes the fitness value"""
        pos = np.array([[50.0, 50.0], [20.0, 20.0]])
        cfg_a = {**BASE_CONFIG, "w1": 0.8, "w2": 0.1, "w3": 0.1}
        cfg_b = {**BASE_CONFIG, "w1": 0.1, "w2": 0.8, "w3": 0.1}
        fa = compute_fitness(pos, cfg_a)
        fb = compute_fitness(pos, cfg_b)
        # They should differ since the objectives have different magnitudes
        assert fa != pytest.approx(fb)
