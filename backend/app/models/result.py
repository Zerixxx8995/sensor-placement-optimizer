"""
models/result.py
----------------
Pydantic data shapes for optimization output and job lifecycle.

Pure data models — no methods, no logic, no HTTP knowledge.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Lifecycle states for an async optimization job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


class JobStatusResponse(BaseModel):
    """Returned by GET /optimize/{job_id}/status."""

    job_id: str
    status: JobStatus


class OptimizationResult(BaseModel):
    """
    Full result returned by GET /optimize/{job_id}/result.
    best_positions is a list of [x, y] pairs.
    coverage_map is a 2D list of float values in [0.0, 1.0].
    fitness_history is one float per iteration (global best).
    """

    job_id: str
    status: JobStatus
    best_positions: list[list[float]] = Field(
        description="List of [x, y] sensor positions"
    )
    coverage_ratio: float = Field(ge=0.0, le=1.0)
    connectivity_ratio: float = Field(ge=0.0, le=1.0)
    avg_energy: float = Field(ge=0.0, le=1.0)
    fitness_history: list[float]
    coverage_map: list[list[float]] = Field(
        description="2D grid of detection probabilities [0.0–1.0]"
    )
    compute_time_seconds: float = Field(ge=0.0)
    iterations_run: int = Field(ge=0)
    gpu_used: bool


class StrategyMetrics(BaseModel):
    """Metrics for a single strategy in a comparison run."""

    strategy: str
    coverage_ratio: float = Field(ge=0.0, le=1.0)
    connectivity_ratio: float = Field(ge=0.0, le=1.0)
    avg_energy: float = Field(ge=0.0, le=1.0)
    compute_time_seconds: float = Field(ge=0.0)


class ComparisonResult(BaseModel):
    """Returned by POST /compare — side-by-side metrics for all strategies."""

    job_id: str
    status: JobStatus
    results: list[StrategyMetrics]


class FaultInjectionResult(BaseModel):
    """Returned by POST /fault-inject."""

    job_id: str
    original_coverage_ratio: float = Field(ge=0.0, le=1.0)
    degraded_coverage_ratio: float = Field(ge=0.0, le=1.0)
    nodes_failed: int = Field(ge=0)
    total_nodes: int = Field(ge=1)
    dropout_percent: float = Field(ge=0.0, le=100.0)
    coverage_map: list[list[float]]
