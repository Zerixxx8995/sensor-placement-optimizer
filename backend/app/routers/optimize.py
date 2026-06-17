"""
routers/optimize.py
---------------------
Layer 1 — URL routing ONLY.

Maps HTTP method + URL pattern to a controller function.
Contains zero logic, zero validation, zero data shaping.
"""

from fastapi import APIRouter, BackgroundTasks

from app.models.config import OptimizationConfig
from app.controllers.optimize_controller import (
    handle_submit,
    handle_status,
    handle_result,
)

router = APIRouter()


@router.post("/optimize", status_code=200)
def post_optimize(config: OptimizationConfig, background_tasks: BackgroundTasks):
    """Submit a new PSO optimization job. Returns job_id immediately."""
    return handle_submit(config, background_tasks)


@router.get("/optimize/{job_id}/status", status_code=200)
def get_status(job_id: str):
    """Poll the lifecycle state of a submitted job."""
    return handle_status(job_id)


@router.get("/optimize/{job_id}/result", status_code=200)
def get_result(job_id: str):
    """Retrieve the full result of a completed job."""
    return handle_result(job_id)
