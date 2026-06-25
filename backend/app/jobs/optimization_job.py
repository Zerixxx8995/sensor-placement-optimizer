"""
jobs/optimization_job.py
-------------------------
Background task wrapper around the PSO core algorithm.

This is the ONLY place that bridges the async job lifecycle (job_store)
with the pure math layer (core/pso.py and core/vdcoa.py). It has no HTTP
knowledge and no business logic — it just runs the algorithm and records
the outcome.
"""

from app.jobs import job_store
from app.core.pso import run_pso
from app.core.pso_gpu import run_pso_gpu
from app.core.vdcoa import run_vdcoa_refinement


def run_optimization_job(job_id: str, config: dict) -> None:
    """
    Execute a PSO (optionally + VDCOA) optimization run as a background task.

    Called by FastAPI BackgroundTasks. Updates job_store at each
    lifecycle transition so the polling endpoints see live status.

    Args:
        job_id: The UUID that was registered in job_store by the service.
        config: Raw dict already shaped for core/pso.run_pso().
    """
    job_store.set_running(job_id)

    def on_iteration(g: int, positions, gbest_pos, gbest_fit) -> None:
        # Publish the iteration updates via the job_store pub/sub queue
        job_store.publish_iteration(job_id, {
            "event": "iteration",
            "iteration": g,
            "best_positions": gbest_pos.tolist(),
            "best_fitness": float(gbest_fit),
            "particles": positions.tolist(),
        })

    try:
        # --- Phase 1: PSO ---
        if config.get("use_gpu"):
            pso_result = run_pso_gpu(config, on_iteration=on_iteration)
        else:
            pso_result = run_pso(config, on_iteration=on_iteration)

        # --- Phase 2: VDCOA refinement (optional) ---
        use_vdcoa = config.get("use_vdcoa", False) or config.get("strategy") == "pso_vdcoa"
        if use_vdcoa:
            pso_iterations = config.get("pso_params", {}).get("iterations", 500)
            chaos_iterations = max(50, pso_iterations // 5)  # 20% of PSO budget

            def on_vdcoa_iteration(i: int, positions, gbest_pos, gbest_fit) -> None:
                g = pso_iterations + i + 1
                job_store.publish_iteration(job_id, {
                    "event": "iteration",
                    "iteration": g,
                    "best_positions": gbest_pos.tolist(),
                    "best_fitness": float(gbest_fit),
                    "particles": positions.tolist(),
                })

            result = run_vdcoa_refinement(
                pso_result,
                config,
                chaos_iterations=chaos_iterations,
                on_iteration=on_vdcoa_iteration,
            )
        else:
            result = pso_result

        job_store.set_complete(job_id, result)
    except Exception as exc:  # noqa: BLE001
        job_store.set_failed(job_id, str(exc))
