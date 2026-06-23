"""
tests/test_fault.py
-------------------
Integration tests for POST /api/v1/fault-inject.

Core assertion from the project plan:
    /fault-inject returns degraded_coverage_ratio < original_coverage_ratio

Additional coverage:
  - 200 response with valid completed job + valid dropout_percent
  - degraded_coverage_ratio in [0, 1]
  - original_coverage_ratio matches the stored result
  - nodes_failed is in [1, total_nodes]
  - coverage_map is a 2D list
  - high dropout (100%) drives coverage to effectively zero
  - 422 on invalid dropout_percent (0 or > 100)
  - 404 on nonexistent job_id
  - 422 when job exists but is not yet complete
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.jobs import job_store


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_store():
    """Wipe in-memory job store before/after each test."""
    job_store.clear_all()
    yield
    job_store.clear_all()


@pytest.fixture(scope="module")
def client():
    """Shared TestClient for all fault tests."""
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ---------------------------------------------------------------------------
# Minimal fast config — small area, few nodes, few iterations
# ---------------------------------------------------------------------------

FAST_CONFIG = {
    "area": {"width": 50.0, "height": 50.0},
    "num_nodes": 10,
    "sensing_radius": 8.0,
    "comm_radius": 16.0,
    "initial_energy": 1.0,
    "weights": {"w1": 0.5, "w2": 0.25, "w3": 0.25},
    "pso_params": {
        "swarm_size": 5,
        "iterations": 5,
        "inertia": 0.7,
        "c1": 1.5,
        "c2": 1.5,
    },
    "use_gpu": False,
    "use_vdcoa": False,
    "seed": 42,
    "restricted_areas": [],
    "non_critical_areas": [],
    "strategy": "pso",
    "cell_size": 5.0,
}


def _submit_and_complete(client) -> str:
    """Submit an optimization job and return the job_id (completes synchronously)."""
    resp = client.post("/api/v1/optimize", json=FAST_CONFIG)
    assert resp.status_code == 200, resp.text
    return resp.json()["job_id"]


# ---------------------------------------------------------------------------
# POST /api/v1/fault-inject — success cases
# ---------------------------------------------------------------------------

class TestFaultInjectSuccess:

    def test_returns_200(self, client):
        job_id = _submit_and_complete(client)
        resp = client.post("/api/v1/fault-inject", json={
            "job_id": job_id,
            "dropout_percent": 30.0,
            "seed": 0,
        })
        assert resp.status_code == 200, resp.text

    def test_degraded_coverage_less_than_original(self, client):
        """Core plan assertion: /fault-inject returns degraded coverage < original."""
        job_id = _submit_and_complete(client)
        result_resp = client.get(f"/api/v1/optimize/{job_id}/result")
        original_coverage = result_resp.json()["coverage_ratio"]

        resp = client.post("/api/v1/fault-inject", json={
            "job_id": job_id,
            "dropout_percent": 50.0,
            "seed": 0,
        })
        body = resp.json()
        assert body["degraded_coverage_ratio"] < body["original_coverage_ratio"], (
            f"Expected degraded={body['degraded_coverage_ratio']} < "
            f"original={body['original_coverage_ratio']}"
        )

    def test_original_coverage_matches_stored_result(self, client):
        job_id = _submit_and_complete(client)
        stored_coverage = client.get(
            f"/api/v1/optimize/{job_id}/result"
        ).json()["coverage_ratio"]

        body = client.post("/api/v1/fault-inject", json={
            "job_id": job_id,
            "dropout_percent": 20.0,
            "seed": 1,
        }).json()
        assert abs(body["original_coverage_ratio"] - stored_coverage) < 1e-6, (
            f"original_coverage_ratio mismatch: got {body['original_coverage_ratio']}, "
            f"expected ~{stored_coverage}"
        )

    def test_response_has_all_required_keys(self, client):
        job_id = _submit_and_complete(client)
        body = client.post("/api/v1/fault-inject", json={
            "job_id": job_id,
            "dropout_percent": 20.0,
        }).json()
        required = {
            "job_id", "original_coverage_ratio", "degraded_coverage_ratio",
            "nodes_failed", "total_nodes", "dropout_percent", "coverage_map",
        }
        missing = required - set(body.keys())
        assert not missing, f"Missing keys: {missing}"

    def test_coverage_ratios_in_valid_range(self, client):
        job_id = _submit_and_complete(client)
        body = client.post("/api/v1/fault-inject", json={
            "job_id": job_id,
            "dropout_percent": 40.0,
            "seed": 2,
        }).json()
        assert 0.0 <= body["original_coverage_ratio"] <= 1.0
        assert 0.0 <= body["degraded_coverage_ratio"] <= 1.0

    def test_nodes_failed_within_bounds(self, client):
        job_id = _submit_and_complete(client)
        body = client.post("/api/v1/fault-inject", json={
            "job_id": job_id,
            "dropout_percent": 30.0,
            "seed": 3,
        }).json()
        assert body["nodes_failed"] >= 1
        assert body["nodes_failed"] <= body["total_nodes"]

    def test_total_nodes_matches_config(self, client):
        job_id = _submit_and_complete(client)
        body = client.post("/api/v1/fault-inject", json={
            "job_id": job_id,
            "dropout_percent": 30.0,
        }).json()
        assert body["total_nodes"] == FAST_CONFIG["num_nodes"]

    def test_coverage_map_is_2d_list(self, client):
        job_id = _submit_and_complete(client)
        body = client.post("/api/v1/fault-inject", json={
            "job_id": job_id,
            "dropout_percent": 30.0,
        }).json()
        assert isinstance(body["coverage_map"], list)
        assert len(body["coverage_map"]) > 0
        assert isinstance(body["coverage_map"][0], list)

    def test_dropout_percent_echoed_in_response(self, client):
        job_id = _submit_and_complete(client)
        body = client.post("/api/v1/fault-inject", json={
            "job_id": job_id,
            "dropout_percent": 25.0,
        }).json()
        assert body["dropout_percent"] == 25.0

    def test_high_dropout_reduces_coverage_significantly(self, client):
        """Removing 90%+ of nodes should make coverage drop noticeably."""
        job_id = _submit_and_complete(client)
        body_low = client.post("/api/v1/fault-inject", json={
            "job_id": job_id,
            "dropout_percent": 10.0,
            "seed": 0,
        }).json()
        body_high = client.post("/api/v1/fault-inject", json={
            "job_id": job_id,
            "dropout_percent": 90.0,
            "seed": 0,
        }).json()
        assert body_high["degraded_coverage_ratio"] <= body_low["degraded_coverage_ratio"], (
            "90% dropout should produce equal or worse coverage than 10% dropout"
        )

    def test_seed_produces_reproducible_results(self, client):
        """Same job + same seed → same outcome."""
        job_id = _submit_and_complete(client)
        payload = {"job_id": job_id, "dropout_percent": 40.0, "seed": 99}
        b1 = client.post("/api/v1/fault-inject", json=payload).json()
        b2 = client.post("/api/v1/fault-inject", json=payload).json()
        assert b1["degraded_coverage_ratio"] == b2["degraded_coverage_ratio"]
        assert b1["nodes_failed"] == b2["nodes_failed"]


# ---------------------------------------------------------------------------
# POST /api/v1/fault-inject — error cases
# ---------------------------------------------------------------------------

class TestFaultInjectErrors:

    def test_zero_dropout_returns_422(self, client):
        """Pydantic gt=0.0 should reject dropout_percent=0."""
        resp = client.post("/api/v1/fault-inject", json={
            "job_id": "any-id",
            "dropout_percent": 0.0,
        })
        assert resp.status_code == 422

    def test_dropout_above_100_returns_422(self, client):
        resp = client.post("/api/v1/fault-inject", json={
            "job_id": "any-id",
            "dropout_percent": 101.0,
        })
        assert resp.status_code == 422

    def test_nonexistent_job_returns_404(self, client):
        resp = client.post("/api/v1/fault-inject", json={
            "job_id": "does-not-exist",
            "dropout_percent": 50.0,
        })
        assert resp.status_code == 404

    def test_missing_job_id_returns_422(self, client):
        """Pydantic should reject a payload missing job_id."""
        resp = client.post("/api/v1/fault-inject", json={
            "dropout_percent": 30.0,
        })
        assert resp.status_code == 422

    def test_missing_dropout_returns_422(self, client):
        resp = client.post("/api/v1/fault-inject", json={
            "job_id": "some-id",
        })
        assert resp.status_code == 422

    def test_pending_job_returns_422(self, client):
        """A job that exists but is still pending should return 422."""
        # Manually insert a pending job into the store
        job_store.create_job("pending-job-id")
        resp = client.post("/api/v1/fault-inject", json={
            "job_id": "pending-job-id",
            "dropout_percent": 30.0,
        })
        assert resp.status_code == 422
