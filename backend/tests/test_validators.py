"""
tests/test_validators.py
------------------------
Unit tests for all three validator modules:
  - validators/optimize_validator.py  (primary focus per build order)
  - validators/compare_validator.py
  - validators/fault_validator.py

Also tests that Pydantic field-level validation (per-field types, ranges)
rejects malformed raw dicts with ValidationError, keeping the validators/
layer responsible only for cross-field rules.

Rule: every bad input must be rejected; every valid input must pass.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.models.config import (
    Area,
    OptimizationConfig,
    PSOParams,
    RestrictedArea,
    Weights,
)
from app.validators.optimize_validator import (
    validate_optimize_config,
    is_valid_optimize_config,
)
from app.validators.compare_validator import validate_compare_config
from app.validators.fault_validator import validate_fault_input


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_valid_config(**overrides) -> OptimizationConfig:
    """Build a valid OptimizationConfig, optionally overriding fields."""
    defaults = dict(
        area=Area(width=200.0, height=200.0),
        num_nodes=20,
        sensing_radius=15.0,
        comm_radius=30.0,
        initial_energy=1.0,
        weights=Weights(w1=0.5, w2=0.25, w3=0.25),
        pso_params=PSOParams(),
        use_gpu=False,
        use_vdcoa=False,
        seed=42,
        restricted_areas=[],
        non_critical_areas=[],
        strategy="pso",
        cell_size=1.0,
    )
    defaults.update(overrides)
    return OptimizationConfig(**defaults)


# ---------------------------------------------------------------------------
# Pydantic field-level validation (type / range guards)
# ---------------------------------------------------------------------------

class TestPydanticFieldValidation:

    def test_negative_area_width_rejected(self):
        with pytest.raises(ValidationError):
            Area(width=-10.0, height=100.0)

    def test_zero_area_height_rejected(self):
        with pytest.raises(ValidationError):
            Area(width=100.0, height=0.0)

    def test_zero_num_nodes_rejected(self):
        with pytest.raises(ValidationError):
            make_valid_config(num_nodes=0)

    def test_negative_sensing_radius_rejected(self):
        with pytest.raises(ValidationError):
            make_valid_config(sensing_radius=-5.0)

    def test_weight_above_one_rejected(self):
        with pytest.raises(ValidationError):
            Weights(w1=1.5, w2=0.0, w3=0.0)

    def test_negative_weight_rejected(self):
        with pytest.raises(ValidationError):
            Weights(w1=-0.1, w2=0.5, w3=0.6)

    def test_negative_inertia_rejected(self):
        with pytest.raises(ValidationError):
            PSOParams(inertia=-0.1)

    def test_zero_iterations_rejected(self):
        with pytest.raises(ValidationError):
            PSOParams(iterations=0)

    def test_valid_config_does_not_raise(self):
        cfg = make_valid_config()
        assert cfg is not None


# ---------------------------------------------------------------------------
# Cross-field: weights must sum to 1
# ---------------------------------------------------------------------------

class TestWeightsSumValidation:

    def test_valid_weights_pass(self):
        cfg = make_valid_config(weights=Weights(w1=0.5, w2=0.25, w3=0.25))
        errors = validate_optimize_config(cfg)
        assert errors == []

    def test_weights_sum_to_zero_rejected(self):
        cfg = make_valid_config(weights=Weights(w1=0.0, w2=0.0, w3=0.0))
        errors = validate_optimize_config(cfg)
        assert any("weights" in e and "1.0" in e for e in errors)

    def test_weights_sum_exceeds_one_rejected(self):
        cfg = make_valid_config(weights=Weights(w1=0.5, w2=0.4, w3=0.4))
        errors = validate_optimize_config(cfg)
        assert any("weights" in e for e in errors)

    def test_weights_sum_below_one_rejected(self):
        cfg = make_valid_config(weights=Weights(w1=0.2, w2=0.2, w3=0.2))
        errors = validate_optimize_config(cfg)
        assert any("weights" in e for e in errors)

    def test_weights_equal_distribution_passes(self):
        cfg = make_valid_config(
            weights=Weights(w1=1/3, w2=1/3, w3=1/3)
        )
        errors = validate_optimize_config(cfg)
        assert errors == []

    def test_all_weight_in_w1_passes(self):
        cfg = make_valid_config(weights=Weights(w1=1.0, w2=0.0, w3=0.0))
        errors = validate_optimize_config(cfg)
        assert errors == []


# ---------------------------------------------------------------------------
# Cross-field: Rs must be < Rc
# ---------------------------------------------------------------------------

class TestSensingCommRadiusValidation:

    def test_rs_less_than_rc_passes(self):
        cfg = make_valid_config(sensing_radius=10.0, comm_radius=20.0)
        errors = validate_optimize_config(cfg)
        assert errors == []

    def test_rs_equals_rc_rejected(self):
        cfg = make_valid_config(sensing_radius=15.0, comm_radius=15.0)
        errors = validate_optimize_config(cfg)
        assert any("sensing_radius" in e or "Rs" in e for e in errors)

    def test_rs_greater_than_rc_rejected(self):
        cfg = make_valid_config(sensing_radius=30.0, comm_radius=15.0)
        errors = validate_optimize_config(cfg)
        assert any("sensing_radius" in e or "Rs" in e for e in errors)

    def test_rs_much_less_than_rc_passes(self):
        cfg = make_valid_config(sensing_radius=1.0, comm_radius=100.0)
        errors = validate_optimize_config(cfg)
        assert errors == []


# ---------------------------------------------------------------------------
# Cross-field: restricted areas within field bounds
# ---------------------------------------------------------------------------

class TestRestrictedAreaValidation:

    def test_valid_ra_within_bounds_passes(self):
        ra = RestrictedArea(x1=10.0, y1=10.0, x2=50.0, y2=50.0)
        cfg = make_valid_config(restricted_areas=[ra])
        errors = validate_optimize_config(cfg)
        assert errors == []

    def test_ra_outside_field_rejected(self):
        ra = RestrictedArea(x1=10.0, y1=10.0, x2=300.0, y2=50.0)  # x2 > 200
        cfg = make_valid_config(restricted_areas=[ra])
        errors = validate_optimize_config(cfg)
        assert any("restricted_areas" in e for e in errors)

    def test_ra_negative_coords_rejected(self):
        ra = RestrictedArea(x1=-5.0, y1=0.0, x2=50.0, y2=50.0)
        cfg = make_valid_config(restricted_areas=[ra])
        errors = validate_optimize_config(cfg)
        assert any("restricted_areas" in e for e in errors)

    def test_ra_inverted_x_coords_rejected(self):
        """x1 >= x2 is invalid"""
        ra = RestrictedArea(x1=80.0, y1=10.0, x2=50.0, y2=50.0)
        cfg = make_valid_config(restricted_areas=[ra])
        errors = validate_optimize_config(cfg)
        assert any("x1" in e and "x2" in e for e in errors)

    def test_ra_inverted_y_coords_rejected(self):
        """y1 >= y2 is invalid"""
        ra = RestrictedArea(x1=10.0, y1=80.0, x2=50.0, y2=50.0)
        cfg = make_valid_config(restricted_areas=[ra])
        errors = validate_optimize_config(cfg)
        assert any("y1" in e and "y2" in e for e in errors)

    def test_multiple_valid_ras_pass(self):
        ras = [
            RestrictedArea(x1=0.0, y1=0.0, x2=50.0, y2=50.0),
            RestrictedArea(x1=100.0, y1=100.0, x2=150.0, y2=150.0),
        ]
        cfg = make_valid_config(restricted_areas=ras)
        errors = validate_optimize_config(cfg)
        assert errors == []


# ---------------------------------------------------------------------------
# Strategy validation
# ---------------------------------------------------------------------------

class TestStrategyValidation:

    def test_valid_strategies_pass(self):
        for strategy in ["pso", "pso_vdcoa", "random", "grid"]:
            cfg = make_valid_config(strategy=strategy)
            errors = validate_optimize_config(cfg)
            assert errors == [], f"Strategy '{strategy}' should be valid"

    def test_unknown_strategy_rejected(self):
        cfg = make_valid_config(strategy="genetic_algorithm")
        errors = validate_optimize_config(cfg)
        assert any("strategy" in e for e in errors)

    def test_empty_strategy_rejected(self):
        cfg = make_valid_config(strategy="")
        errors = validate_optimize_config(cfg)
        assert any("strategy" in e for e in errors)


# ---------------------------------------------------------------------------
# Cell size validation
# ---------------------------------------------------------------------------

class TestCellSizeValidation:

    def test_valid_cell_size_passes(self):
        cfg = make_valid_config(cell_size=2.0)
        errors = validate_optimize_config(cfg)
        assert errors == []

    def test_cell_size_larger_than_field_rejected(self):
        cfg = make_valid_config(
            area=Area(width=50.0, height=50.0),
            cell_size=60.0,
        )
        errors = validate_optimize_config(cfg)
        assert any("cell_size" in e for e in errors)


# ---------------------------------------------------------------------------
# is_valid_optimize_config convenience wrapper
# ---------------------------------------------------------------------------

class TestIsValidWrapper:

    def test_valid_config_returns_true(self):
        cfg = make_valid_config()
        assert is_valid_optimize_config(cfg) is True

    def test_invalid_config_returns_false(self):
        cfg = make_valid_config(weights=Weights(w1=0.0, w2=0.0, w3=0.0))
        assert is_valid_optimize_config(cfg) is False


# ---------------------------------------------------------------------------
# Multiple errors returned at once
# ---------------------------------------------------------------------------

class TestMultipleErrors:

    def test_multiple_bad_fields_all_reported(self):
        """A config with multiple errors should return multiple error messages."""
        cfg = make_valid_config(
            weights=Weights(w1=0.0, w2=0.0, w3=0.0),   # weights != 1
            sensing_radius=50.0,                          # Rs > Rc
            comm_radius=20.0,
        )
        errors = validate_optimize_config(cfg)
        assert len(errors) >= 2, f"Expected >= 2 errors, got {len(errors)}: {errors}"


# ---------------------------------------------------------------------------
# Compare validator
# ---------------------------------------------------------------------------

class TestCompareValidator:

    def test_valid_strategies_pass(self):
        cfg = make_valid_config()
        errors = validate_compare_config(cfg, ["pso", "random"])
        assert errors == []

    def test_empty_strategies_rejected(self):
        cfg = make_valid_config()
        errors = validate_compare_config(cfg, [])
        assert any("strategy" in e or "least one" in e for e in errors)

    def test_unknown_strategy_rejected(self):
        cfg = make_valid_config()
        errors = validate_compare_config(cfg, ["neural_net"])
        assert any("neural_net" in e for e in errors)

    def test_base_config_errors_also_surfaced(self):
        """Bad base config errors bubble up through compare validator."""
        cfg = make_valid_config(weights=Weights(w1=0.0, w2=0.0, w3=0.0))
        errors = validate_compare_config(cfg, ["pso"])
        assert any("weights" in e for e in errors)


# ---------------------------------------------------------------------------
# Fault validator
# ---------------------------------------------------------------------------

class TestFaultValidator:

    def test_valid_input_passes(self):
        errors = validate_fault_input("job-abc123", 30.0)
        assert errors == []

    def test_empty_job_id_rejected(self):
        errors = validate_fault_input("", 30.0)
        assert any("job_id" in e for e in errors)

    def test_whitespace_job_id_rejected(self):
        errors = validate_fault_input("   ", 30.0)
        assert any("job_id" in e for e in errors)

    def test_zero_dropout_rejected(self):
        errors = validate_fault_input("job-abc", 0.0)
        assert any("dropout" in e for e in errors)

    def test_negative_dropout_rejected(self):
        errors = validate_fault_input("job-abc", -10.0)
        assert any("dropout" in e for e in errors)

    def test_hundred_percent_dropout_passes(self):
        errors = validate_fault_input("job-abc", 100.0)
        assert errors == []

    def test_over_hundred_percent_rejected(self):
        errors = validate_fault_input("job-abc", 101.0)
        assert any("dropout" in e for e in errors)
