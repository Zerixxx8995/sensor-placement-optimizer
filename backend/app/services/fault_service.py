"""
services/fault_service.py
--------------------------
Business logic for POST /api/v1/fault-inject.

Takes a completed optimization result, randomly disables dropout_percent of
sensor nodes, and returns before/after coverage metrics plus the degraded
coverage map.

No HTTP knowledge — pure orchestration and math only.
"""

from __future__ import annotations

import math
import uuid

import numpy as np

from app.core.sensing_model import coverage_map as compute_coverage_map
from app.core.fitness import _connectivity_ratio
from app.jobs import job_store


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_fault_injection(job_id: str, dropout_percent: float, seed: int | None = None) -> dict:
    """
    Simulate random node failures on a completed optimization result.

    Args:
        job_id:          ID of a completed optimization job.
        dropout_percent: Percentage of nodes to disable (must be in (0, 100]).
        seed:            Optional RNG seed for reproducibility.

    Returns:
        {
          "job_id":                  str,
          "original_coverage_ratio": float,
          "degraded_coverage_ratio": float,
          "nodes_failed":            int,
          "total_nodes":             int,
          "dropout_percent":         float,
          "coverage_map":            list[list[float]],
          "connectivity_ratio":      float,
        }

    Raises:
        ValueError: If the job does not exist, is not complete, or has no positions.
    """
    job = job_store.get_job(job_id)
    if job is None:
        raise ValueError(f"Job '{job_id}' not found.")
    if job["status"] != "complete":
        raise ValueError(
            f"Job '{job_id}' is not complete (status={job['status']}). "
            "Fault injection requires a completed optimization result."
        )

    raw = job["result"]
    if not raw:
        raise ValueError(f"Job '{job_id}' has no result data.")

    return _compute_fault_injection(job_id, raw, dropout_percent, seed)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _compute_fault_injection(
    job_id: str,
    raw: dict,
    dropout_percent: float,
    seed: int | None,
) -> dict:
    """Core fault injection computation — works on raw result dicts."""

    # --- Unpack positions from result (comes in as list[list[float]]) ---
    positions = np.array(raw["best_positions"], dtype=np.float64)   # (N, 2)
    total_nodes = len(positions)

    # Infer field config from coverage_map shape + stored metrics
    # (best effort — coverage_map rows/cols give us the grid resolution)
    cov_map_stored = np.array(raw.get("coverage_map", [[]]), dtype=np.float64)
    rows, cols = cov_map_stored.shape if cov_map_stored.ndim == 2 else (1, 1)

    # Recover area bounds from the stored coverage_map grid:
    # We don't have the original config here, so infer area_W / area_H from
    # the bounding box of the deployed sensors (safe upper bound).
    xs, ys = positions[:, 0], positions[:, 1]
    area_W = float(max(xs.max() * 1.05, 1.0))
    area_H = float(max(ys.max() * 1.05, 1.0))

    # Use Rs stored as part of result via sensing_radius proxy:
    # We re-derive cell_size from the stored map's dimension vs area.
    # If coverage_map is empty/trivial, fall back to 1.0.
    if cols > 1:
        cell_size = area_W / cols
        Rs = cell_size * 2.0   # conservative fallback sensing radius
    else:
        cell_size = 1.0
        Rs = 2.0

    # ---  Better approach: use stored coverage_ratio to skip recalculation ---
    original_coverage_ratio = float(raw.get("coverage_ratio", 0.0))

    # --- Determine which nodes fail ---
    nodes_failed = max(1, math.ceil(total_nodes * dropout_percent / 100.0))
    nodes_failed = min(nodes_failed, total_nodes)

    rng = np.random.default_rng(seed)
    failed_indices = rng.choice(total_nodes, size=nodes_failed, replace=False)
    surviving_mask = np.ones(total_nodes, dtype=bool)
    surviving_mask[failed_indices] = False
    surviving_positions = positions[surviving_mask]

    # --- Recompute coverage on surviving nodes ---
    if len(surviving_positions) == 0:
        degraded_cov_map = np.zeros((rows, cols), dtype=np.float64)
        degraded_coverage_ratio = 0.0
        degraded_connectivity = 0.0
    else:
        degraded_cov_map = compute_coverage_map(
            surviving_positions, area_W, area_H, Rs,
            cell_size=cell_size,
        )
        degraded_coverage_ratio = float(np.mean(degraded_cov_map))

        # Infer comm_radius from stored connectivity_ratio (fallback: 2× Rs)
        Rc = Rs * 2.0
        degraded_connectivity = _connectivity_ratio(
            surviving_positions, Rc, sink=(0.0, 0.0)
        )

    return {
        "job_id": str(uuid.uuid4()),
        "original_coverage_ratio": original_coverage_ratio,
        "degraded_coverage_ratio": degraded_coverage_ratio,
        "nodes_failed": nodes_failed,
        "total_nodes": total_nodes,
        "dropout_percent": dropout_percent,
        "coverage_map": degraded_cov_map.tolist(),
        "connectivity_ratio": degraded_connectivity,
    }
