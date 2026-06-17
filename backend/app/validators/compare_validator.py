"""
validators/compare_validator.py
--------------------------------
Input validation for POST /api/v1/compare.

The compare endpoint accepts the same OptimizationConfig but also requires
at least one strategy to be selected. Reuses the optimize validator for
shared rules and adds compare-specific checks.
"""

from __future__ import annotations

from app.models.config import OptimizationConfig
from app.validators.optimize_validator import validate_optimize_config

ALLOWED_STRATEGIES = {"pso", "pso_vdcoa", "random", "grid"}


def validate_compare_config(config: OptimizationConfig, strategies: list[str]) -> list[str]:
    """
    Validate input for the compare endpoint.

    Args:
        config:     Parsed OptimizationConfig.
        strategies: List of strategy names the user selected.

    Returns:
        List of error strings. Empty = valid.
    """
    errors = validate_optimize_config(config)

    if not strategies:
        errors.append(
            "At least one strategy must be selected for comparison. "
            f"Allowed values: {sorted(ALLOWED_STRATEGIES)}."
        )

    unknown = [s for s in strategies if s not in ALLOWED_STRATEGIES]
    for s in unknown:
        errors.append(
            f"Unknown strategy '{s}'. Allowed values: {sorted(ALLOWED_STRATEGIES)}."
        )

    return errors
