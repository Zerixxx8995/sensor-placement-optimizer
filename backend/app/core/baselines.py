"""
core/baselines.py
-----------------
Non-optimized sensor placement baselines for comparison.

Two strategies:
  - random: N sensors placed uniformly at random within [0,W] x [0,H].
  - grid:   N sensors on a regular rectangular grid, aspect-ratio-preserving.

Both return the same result dict contract as core/pso.run_pso() so that the
comparison service can treat all four strategies uniformly.

No I/O, no HTTP, no business logic — pure placement algorithms.
"""

from __future__ import annotations

import time

import numpy as np

from .sensing_model import coverage_map as compute_coverage_map
from .fitness import _connectivity_ratio, _energy_cost


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _compute_metrics(
    positions: np.ndarray,
    area_W: float,
    area_H: float,
    Rs: float,
    Rc: float,
    lam: float,
    cell_size: float,
    sink: tuple,
    restricted_mask,
) -> tuple[np.ndarray, float, float, float]:
    """Shared metric computation for all baseline strategies."""
    cov_map = compute_coverage_map(
        positions, area_W, area_H, Rs, lam, cell_size, restricted_mask
    )
    if restricted_mask is not None:
        valid = ~restricted_mask
        coverage_ratio = float(np.mean(cov_map[valid])) if valid.any() else 0.0
    else:
        coverage_ratio = float(np.mean(cov_map))

    connectivity_ratio = float(_connectivity_ratio(positions, Rc, sink))
    avg_energy = float(_energy_cost(positions, area_W, area_H))
    return cov_map, coverage_ratio, connectivity_ratio, avg_energy


def _unpack(config: dict):
    """Extract and type-cast all fields needed by both strategies."""
    area = config["area"]
    return (
        float(area["width"]),
        float(area["height"]),
        int(config["num_nodes"]),
        float(config["sensing_radius"]),
        float(config["comm_radius"]),
        float(config.get("lam", 0.5)),
        float(config.get("cell_size", 1.0)),
        tuple(config.get("sink", (0.0, 0.0))),
        config.get("restricted_mask", None),
        config.get("seed", None),
    )


# ---------------------------------------------------------------------------
# Public strategies
# ---------------------------------------------------------------------------

def place_random(config: dict) -> dict:
    """
    Random placement baseline.

    Sensors are drawn independently and uniformly from the deployment area.
    Seeded for reproducibility when config["seed"] is set.
    """
    area_W, area_H, N, Rs, Rc, lam, cell_size, sink, restricted_mask, seed = _unpack(config)
    rng = np.random.default_rng(seed)

    t_start = time.perf_counter()
    positions = rng.uniform(low=[0.0, 0.0], high=[area_W, area_H], size=(N, 2))
    compute_time = time.perf_counter() - t_start

    cov_map, cov_ratio, conn_ratio, energy = _compute_metrics(
        positions, area_W, area_H, Rs, Rc, lam, cell_size, sink, restricted_mask
    )

    return {
        "strategy": "random",
        "best_positions": positions,
        "fitness_history": [],
        "coverage_map": cov_map,
        "coverage_ratio": cov_ratio,
        "connectivity_ratio": conn_ratio,
        "avg_energy": energy,
        "compute_time_seconds": compute_time,
        "iterations_run": 0,
        "gpu_used": False,
    }


def place_grid(config: dict) -> dict:
    """
    Regular-grid placement baseline.

    Computes rows × cols that best matches the field's aspect ratio and N,
    then places sensors at cell centres. Extra cells are discarded so that
    exactly N sensors are returned.
    """
    area_W, area_H, N, Rs, Rc, lam, cell_size, sink, restricted_mask, _ = _unpack(config)

    t_start = time.perf_counter()

    # Aspect-ratio-preserving grid: cols/rows ≈ W/H
    aspect = area_W / area_H if area_H > 0 else 1.0
    rows = max(1, int(round(np.sqrt(N / aspect))))
    cols = max(1, int(round(aspect * rows)))

    # Ensure we have at least N cells; add cols if short
    while rows * cols < N:
        cols += 1

    x_step = area_W / cols
    y_step = area_H / rows

    pts: list[list[float]] = []
    for r in range(rows):
        for c in range(cols):
            pts.append([(c + 0.5) * x_step, (r + 0.5) * y_step])
            if len(pts) == N:
                break
        if len(pts) == N:
            break

    positions = np.array(pts[:N], dtype=np.float64)
    compute_time = time.perf_counter() - t_start

    cov_map, cov_ratio, conn_ratio, energy = _compute_metrics(
        positions, area_W, area_H, Rs, Rc, lam, cell_size, sink, restricted_mask
    )

    return {
        "strategy": "grid",
        "best_positions": positions,
        "fitness_history": [],
        "coverage_map": cov_map,
        "coverage_ratio": cov_ratio,
        "connectivity_ratio": conn_ratio,
        "avg_energy": energy,
        "compute_time_seconds": compute_time,
        "iterations_run": 0,
        "gpu_used": False,
    }
