"""
validators/fault_validator.py
------------------------------
Input validation for POST /api/v1/fault-inject.

Checks that the dropout percentage is in (0, 100] and that the provided
job_id is a non-empty string.
"""

from __future__ import annotations


def validate_fault_input(job_id: str, dropout_percent: float) -> list[str]:
    """
    Validate inputs for the fault injection endpoint.

    Args:
        job_id:          ID of the completed optimization job.
        dropout_percent: Percentage of nodes to disable (must be in (0, 100]).

    Returns:
        List of error strings. Empty = valid.
    """
    errors: list[str] = []

    if not job_id or not job_id.strip():
        errors.append("job_id must be a non-empty string.")

    if not (0.0 < dropout_percent <= 100.0):
        errors.append(
            f"dropout_percent must be in the range (0, 100], got {dropout_percent}."
        )

    return errors
