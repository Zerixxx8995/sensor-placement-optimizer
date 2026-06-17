"""
controllers/optimize_controller.py
------------------------------------
Request / response handling for the optimize endpoints.

Responsibilities (and ONLY these):
  - Parse the validated Pydantic model from the request body.
  - Run cross-field validation via the validator layer.
  - Call the service layer.
  - Shape the JSON response dict.
  - Raise HTTPException for validation failures or missing resources.

No business logic, no algorithm code, no direct DB/store access.
"""

import numpy as np
from fastapi import BackgroundTasks, HTTPException

from app.models.config import OptimizationConfig
from app.validators.optimize_validator import validate_optimize_config
from app.services import optimization_service


def handle_submit(
    config: OptimizationConfig, background_tasks: BackgroundTasks
) -> dict:
    """
    POST /optimize — validate → submit → return job_id.
    Raises 422 if cross-field rules fail.
    """
    errors = validate_optimize_config(config)
    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})

    job_id = optimization_service.submit_optimization(config, background_tasks)
    return {"job_id": job_id, "status": "pending"}


def handle_status(job_id: str) -> dict:
    """
    GET /optimize/{job_id}/status — return current job lifecycle state.
    Raises 404 if job_id is unknown.
    """
    job = optimization_service.get_job_status(job_id)
    if job is None:
        raise HTTPException(
            status_code=404, detail=f"Job '{job_id}' not found."
        )
    return {"job_id": job_id, "status": job["status"]}


def handle_result(job_id: str) -> dict:
    """
    GET /optimize/{job_id}/result — return full result when complete.
    Raises 404 if unknown, 202 if still in-progress, 500 if failed.
    """
    job = optimization_service.get_job_status(job_id)
    if job is None:
        raise HTTPException(
            status_code=404, detail=f"Job '{job_id}' not found."
        )

    status = job["status"]

    if status in ("pending", "running"):
        raise HTTPException(
            status_code=202,
            detail=f"Job is not complete yet. Current status: {status}",
        )

    if status == "failed":
        raise HTTPException(
            status_code=500,
            detail=f"Job failed: {job.get('error', 'unknown error')}",
        )

    # status == "complete"
    raw = job["result"]
    return {
        "job_id": job_id,
        "status": "complete",
        "best_positions": _to_list(raw["best_positions"]),
        "coverage_ratio": float(raw["coverage_ratio"]),
        "connectivity_ratio": float(raw["connectivity_ratio"]),
        "avg_energy": float(raw["avg_energy"]),
        "fitness_history": [float(f) for f in raw["fitness_history"]],
        "coverage_map": _to_list(raw["coverage_map"]),
        "compute_time_seconds": float(raw["compute_time_seconds"]),
        "iterations_run": int(raw["iterations_run"]),
        "gpu_used": bool(raw["gpu_used"]),
    }


def _to_list(value):
    """Convert numpy arrays to nested Python lists for JSON serialisation."""
    if isinstance(value, np.ndarray):
        return value.tolist()
    return value
