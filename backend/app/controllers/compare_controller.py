"""
controllers/compare_controller.py
-----------------------------------
Request / response handling for POST /api/v1/compare.

Responsibilities:
  - Accept the validated Pydantic model.
  - Run cross-field validation via the validator layer.
  - Call comparison_service.run_comparison().
  - Return the shaped response dict.
  - Raise HTTPException for validation failures.

No business logic, no algorithm code.
"""

from __future__ import annotations

from fastapi import HTTPException

from app.models.config import OptimizationConfig
from app.validators.compare_validator import validate_compare_config
from app.services import comparison_service

# All four strategies are always run in a comparison
_ALL_STRATEGIES = ["random", "grid", "pso", "pso_vdcoa"]


def handle_compare(config: OptimizationConfig) -> dict:
    """
    POST /compare — validate config → run all strategies → return table.
    Raises 422 if cross-field validation fails.
    """
    errors = validate_compare_config(config, _ALL_STRATEGIES)
    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})

    return comparison_service.run_comparison(config)
