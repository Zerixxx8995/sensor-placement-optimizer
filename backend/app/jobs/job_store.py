"""
jobs/job_store.py
-----------------
In-memory job registry. Maps job_id → {status, result, error}.

Thread-safe via threading.Lock so FastAPI BackgroundTasks (which run in
worker threads) can safely write while request threads read.

No I/O, no HTTP, no business logic — pure state storage.
"""

import threading
from typing import Any

# Module-level store — lives for the lifetime of the process.
_store: dict[str, dict[str, Any]] = {}
_lock = threading.Lock()


def create_job(job_id: str) -> None:
    """Register a new job in PENDING state."""
    with _lock:
        _store[job_id] = {
            "status": "pending",
            "result": None,
            "error": None,
        }


def get_job(job_id: str) -> dict[str, Any] | None:
    """Return the job record or None if not found. Returns a shallow copy."""
    with _lock:
        record = _store.get(job_id)
        return dict(record) if record is not None else None


def set_running(job_id: str) -> None:
    """Transition job to RUNNING state."""
    with _lock:
        if job_id in _store:
            _store[job_id]["status"] = "running"


def set_complete(job_id: str, result: dict[str, Any]) -> None:
    """Transition job to COMPLETE and store its result payload."""
    with _lock:
        if job_id in _store:
            _store[job_id]["status"] = "complete"
            _store[job_id]["result"] = result


def set_failed(job_id: str, error: str) -> None:
    """Transition job to FAILED and record the error message."""
    with _lock:
        if job_id in _store:
            _store[job_id]["status"] = "failed"
            _store[job_id]["error"] = error


def clear_all() -> None:
    """
    Wipe the entire store. Intended for use in tests only.
    Not exposed via any API endpoint.
    """
    with _lock:
        _store.clear()
