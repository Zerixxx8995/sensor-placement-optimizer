"""
services/comparison_service.py
--------------------------------
Business logic for the /compare endpoint.

Runs all four placement strategies on the same config and assembles a
unified comparison result. Strategy results are normalised into StrategyMetrics
dicts so the comparison table is uniform regardless of which algorithm produced them.

Strategies run (in order):
  1. random      — core/baselines.place_random()
  2. grid        — core/baselines.place_grid()
  3. pso         — core/pso.run_pso()
  4. pso_vdcoa   — core/pso.run_pso() for MVP (VDCOA chaos refinement in Step 16)

No HTTP knowledge — pure orchestration only.
"""

from __future__ import annotations

import uuid

from app.models.config import OptimizationConfig
from app.core.baselines import place_random, place_grid
from app.core.pso import run_pso


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_comparison(config: OptimizationConfig) -> dict:
    """
    Run all four strategies synchronously and return a comparison dict.

    Args:
        config: Validated OptimizationConfig (cross-field checks already done).

    Returns:
        {
          "job_id":  str,
          "status":  "complete",
          "results": [StrategyMetrics × 4]
        }
    """
    pso_cfg = _to_pso_config(config)

    results = [
        _extract_metrics("random",    place_random(pso_cfg)),
        _extract_metrics("grid",      place_grid(pso_cfg)),
        _extract_metrics("pso",       run_pso(pso_cfg)),
        # PSO-VDCOA runs standard PSO until core/vdcoa.py is integrated (Step 16)
        _extract_metrics("pso_vdcoa", run_pso({**pso_cfg, "seed": (pso_cfg.get("seed") or 0) + 1})),
    ]

    return {
        "job_id": str(uuid.uuid4()),
        "status": "complete",
        "results": results,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_metrics(strategy: str, result: dict) -> dict:
    """Pull the four comparison metrics out of any strategy result dict."""
    return {
        "strategy": strategy,
        "coverage_ratio": float(result["coverage_ratio"]),
        "connectivity_ratio": float(result["connectivity_ratio"]),
        "avg_energy": float(result["avg_energy"]),
        "compute_time_seconds": float(result["compute_time_seconds"]),
    }


def _to_pso_config(config: OptimizationConfig) -> dict:
    """Translate Pydantic OptimizationConfig into the raw dict core expects."""
    return {
        "area": {"width": config.area.width, "height": config.area.height},
        "num_nodes": config.num_nodes,
        "sensing_radius": config.sensing_radius,
        "comm_radius": config.comm_radius,
        "initial_energy": config.initial_energy,
        "weights": {
            "w1": config.weights.w1,
            "w2": config.weights.w2,
            "w3": config.weights.w3,
        },
        "pso_params": {
            "swarm_size": config.pso_params.swarm_size,
            "iterations": config.pso_params.iterations,
            "inertia": config.pso_params.inertia,
            "c1": config.pso_params.c1,
            "c2": config.pso_params.c2,
        },
        "seed": config.seed,
        "restricted_areas": [ra.model_dump() for ra in config.restricted_areas],
        "non_critical_areas": [nca.model_dump() for nca in config.non_critical_areas],
        "cell_size": config.cell_size,
    }
