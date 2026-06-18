"""
tests/test_middleware.py
------------------------
Unit and integration tests for:
  - middleware/request_logger.py  (RequestLoggerMiddleware)
  - middleware/error_handler.py   (add_error_handlers)

Uses a self-contained mini FastAPI app so these tests are completely
independent of the main app's routes and services.

Tests the full contract required by the build order:
  - Every response has an X-Request-ID header (auto-generated)
  - X-Request-ID is echoed from the request if the client provided one
  - Unhandled exceptions return HTTP 500 with a JSON body
  - The 500 JSON body has "error", "detail", and "request_id" keys
  - RequestValidationError returns 422 with a JSON body (same envelope)
  - Normal 200 responses still carry X-Request-ID
  - The request_id in the error body matches the X-Request-ID header value
"""

from __future__ import annotations

import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel
from fastapi import Body
from typing import Annotated

from app.middleware.error_handler import add_error_handlers
from app.middleware.request_logger import RequestLoggerMiddleware, REQUEST_ID_HEADER


# Module-level model (FastAPI 0.137+ requires models at module scope for
# correct body-parameter resolution with Annotated)
class _Item(BaseModel):
    name: str
    value: int


# ---------------------------------------------------------------------------
# Minimal test application
# ---------------------------------------------------------------------------

def _build_test_app() -> FastAPI:
    """
    Create a tiny FastAPI app with both middleware applied.
    Routes are kept minimal and completely independent of the main app.
    """
    mini = FastAPI()

    # Apply same middleware as the main app
    mini.add_middleware(RequestLoggerMiddleware)
    add_error_handlers(mini)

    # ── Routes ────────────────────────────────────────────────────────────

    @mini.get("/ok")
    def ok_route():
        return {"status": "ok"}

    @mini.post("/items")
    def create_item(item: Annotated[_Item, Body()]):
        return {"received": item.model_dump()}

    @mini.get("/crash")
    def crash_route():
        raise RuntimeError("Deliberate crash for testing error handler")

    @mini.get("/crash-value-error")
    def crash_value_error():
        raise ValueError("Bad value deliberately raised")

    @mini.get("/divide-by-zero")
    def divide():
        return 1 / 0  # ZeroDivisionError

    return mini


_TEST_APP = _build_test_app()


@pytest.fixture(scope="module")
def client():
    """TestClient that does NOT re-raise server exceptions (needed for 500 tests)."""
    with TestClient(_TEST_APP, raise_server_exceptions=False) as c:
        yield c


# ---------------------------------------------------------------------------
# X-Request-ID injection (RequestLoggerMiddleware)
# ---------------------------------------------------------------------------

class TestRequestIDInjection:

    def test_ok_response_has_request_id_header(self, client):
        resp = client.get("/ok")
        assert REQUEST_ID_HEADER in resp.headers, (
            f"Expected '{REQUEST_ID_HEADER}' in response headers"
        )

    def test_request_id_is_non_empty_string(self, client):
        resp = client.get("/ok")
        rid = resp.headers.get(REQUEST_ID_HEADER, "")
        assert len(rid) > 0

    def test_request_id_is_valid_uuid_when_auto_generated(self, client):
        """When client sends no X-Request-ID, the middleware generates a UUID4."""
        resp = client.get("/ok")
        rid = resp.headers[REQUEST_ID_HEADER]
        # UUID4 can be parsed without error
        parsed = uuid.UUID(rid)
        assert parsed.version == 4

    def test_client_provided_request_id_is_echoed(self, client):
        """If the client sends X-Request-ID, the same value must appear in the response."""
        custom_id = "my-trace-abc-123"
        resp = client.get("/ok", headers={REQUEST_ID_HEADER: custom_id})
        assert resp.headers[REQUEST_ID_HEADER] == custom_id

    def test_each_request_gets_unique_id(self, client):
        rid1 = client.get("/ok").headers[REQUEST_ID_HEADER]
        rid2 = client.get("/ok").headers[REQUEST_ID_HEADER]
        assert rid1 != rid2

    def test_404_response_has_request_id(self, client):
        """Even a 404 from a non-existent route must carry X-Request-ID."""
        resp = client.get("/this-does-not-exist")
        assert REQUEST_ID_HEADER in resp.headers

    def test_500_response_has_request_id(self, client):
        resp = client.get("/crash")
        assert REQUEST_ID_HEADER in resp.headers

    def test_422_response_has_request_id(self, client):
        """Bad JSON body → 422; header must still be present."""
        resp = client.post("/items", json={"name": "x", "value": "not-an-int"})
        assert REQUEST_ID_HEADER in resp.headers


# ---------------------------------------------------------------------------
# 500 error handler (add_error_handlers → Exception catch-all)
# ---------------------------------------------------------------------------

class TestErrorHandler500:

    def test_crash_returns_500(self, client):
        resp = client.get("/crash")
        assert resp.status_code == 500

    def test_crash_returns_json_content_type(self, client):
        resp = client.get("/crash")
        assert "application/json" in resp.headers.get("content-type", "")

    def test_500_body_has_error_key(self, client):
        body = client.get("/crash").json()
        assert "error" in body

    def test_500_body_has_detail_key(self, client):
        body = client.get("/crash").json()
        assert "detail" in body

    def test_500_body_has_request_id_key(self, client):
        body = client.get("/crash").json()
        assert "request_id" in body

    def test_500_body_error_is_string(self, client):
        body = client.get("/crash").json()
        assert isinstance(body["error"], str)

    def test_500_body_detail_contains_exception_message(self, client):
        body = client.get("/crash").json()
        assert "Deliberate crash" in body["detail"]

    def test_500_request_id_matches_header(self, client):
        """The request_id in the JSON body must match the X-Request-ID header."""
        custom_id = "test-correlation-id"
        resp = client.get("/crash", headers={REQUEST_ID_HEADER: custom_id})
        body = resp.json()
        assert body["request_id"] == custom_id
        assert resp.headers[REQUEST_ID_HEADER] == custom_id

    def test_value_error_returns_500(self, client):
        resp = client.get("/crash-value-error")
        assert resp.status_code == 500

    def test_zero_division_returns_500(self, client):
        resp = client.get("/divide-by-zero")
        assert resp.status_code == 500

    def test_zero_division_detail_not_empty(self, client):
        body = client.get("/divide-by-zero").json()
        assert len(body.get("detail", "")) > 0


# ---------------------------------------------------------------------------
# 422 validation error handler
# ---------------------------------------------------------------------------

class TestErrorHandler422:

    def test_bad_payload_returns_422(self, client):
        resp = client.post("/items", json={"name": "x", "value": "not-an-int"})
        assert resp.status_code == 422

    def test_422_body_has_error_key(self, client):
        body = client.post("/items", json={"name": "x", "value": "bad"}).json()
        assert "error" in body

    def test_422_body_has_detail_key(self, client):
        body = client.post("/items", json={"name": "x", "value": "bad"}).json()
        assert "detail" in body

    def test_422_body_has_request_id_key(self, client):
        body = client.post("/items", json={"name": "x", "value": "bad"}).json()
        assert "request_id" in body

    def test_422_detail_is_list(self, client):
        body = client.post("/items", json={"name": "x", "value": "bad"}).json()
        assert isinstance(body["detail"], list)

    def test_missing_required_field_returns_422(self, client):
        resp = client.post("/items", json={"name": "only-name"})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Normal requests still work after middleware is applied
# ---------------------------------------------------------------------------

class TestNormalFlowUnaffected:

    def test_ok_route_returns_200(self, client):
        resp = client.get("/ok")
        assert resp.status_code == 200

    def test_ok_route_returns_json(self, client):
        resp = client.get("/ok")
        assert resp.json() == {"status": "ok"}

    def test_post_route_returns_200(self, client):
        resp = client.post("/items", json={"name": "sensor", "value": 42})
        assert resp.status_code == 200

    def test_post_route_echoes_payload(self, client):
        resp = client.post("/items", json={"name": "sensor", "value": 42})
        assert resp.json()["received"] == {"name": "sensor", "value": 42}


# ---------------------------------------------------------------------------
# Regression: existing main-app routes still work with middleware applied
# ---------------------------------------------------------------------------

class TestMainAppRegressionWithMiddleware:
    """
    Sanity-check that wiring middleware into main.py didn't break anything.
    Imports the real app (with middleware) via TestClient.
    """

    @pytest.fixture(scope="class")
    @classmethod
    def main_client(cls, tmp_path_factory):
        from app.main import app
        from app.jobs import job_store
        job_store.clear_all()
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c
        job_store.clear_all()

    def test_health_still_200(self, main_client):
        resp = main_client.get("/api/v1/health")
        assert resp.status_code == 200

    def test_health_has_request_id_header(self, main_client):
        resp = main_client.get("/api/v1/health")
        assert REQUEST_ID_HEADER in resp.headers

    def test_optimize_still_accepts_valid_request(self, main_client):
        payload = {
            "area": {"width": 50.0, "height": 50.0},
            "num_nodes": 3,
            "sensing_radius": 8.0,
            "comm_radius": 16.0,
            "initial_energy": 1.0,
            "weights": {"w1": 0.5, "w2": 0.25, "w3": 0.25},
            "pso_params": {"swarm_size": 3, "iterations": 2},
            "seed": 1,
            "cell_size": 5.0,
        }
        resp = main_client.post("/api/v1/optimize", json=payload)
        assert resp.status_code == 200
        assert REQUEST_ID_HEADER in resp.headers
