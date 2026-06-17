"""
jobs/optimization_job.py
-------------------------
Background task wrapper around the PSO core algorithm.

This is the ONLY place that bridges the async job lifecycle (job_store)
with the pure math layer (core/pso.py). It has no HTTP knowledge and
no business logic — it just runs the algorithm and records the outcome.
"""

from app.jobs import job_store
from app.core.pso import run_pso


def run_optimization_job(job_id: str, config: dict) -> None:
    """
    Execute a PSO optimization run as a background task.

    Called by FastAPI BackgroundTasks. Updates job_store at each
    lifecycle transition so the polling endpoints see live status.

    Args:
        job_id: The UUID that was registered in job_store by the service.
        config: Raw dict already shaped for core/pso.run_pso().
    """
    job_store.set_running(job_id)
    try:
        result = run_pso(config)
        job_store.set_complete(job_id, result)
    except Exception as exc:  # noqa: BLE001
        job_store.set_failed(job_id, str(exc))
