"""
routers/compare.py
-------------------
Layer 1 — URL routing ONLY for the compare endpoint.
Zero logic, zero validation, zero data shaping.
"""

from fastapi import APIRouter

from app.models.config import OptimizationConfig
from app.controllers.compare_controller import handle_compare

router = APIRouter()


@router.post("/compare", status_code=200)
def post_compare(config: OptimizationConfig):
    """
    Run all four strategies (Random, Grid, PSO, PSO-VDCOA) on the same
    configuration and return a side-by-side comparison table.
    """
    return handle_compare(config)
