"""Tests for the environment-driven CORS configuration."""

import pytest
from fastapi.testclient import TestClient

from sentinel_spr019.api.cors import ORIGINS_ENV_VAR, parse_origins
from sentinel_spr019.api.main import create_app

DASHBOARD = "https://dashboard.example.com"
LOCALHOST = "http://localhost:5173"


class TestParseOrigins:
    @pytest.mark.parametrize("raw", [None, "", "   ", ",", " , , "])
    def test_blank_input_yields_no_origins(self, raw):
        assert parse_origins(raw) == []

    def test_entries_are_split_and_trimmed(self):
        assert parse_origins(f" {LOCALHOST} , {DASHBOARD} ") == [LOCALHOST, DASHBOARD]

    def test_trailing_slashes_are_normalised(self):
        assert parse_origins(f"{DASHBOARD}/") == [DASHBOARD]

    def test_duplicates_are_collapsed_preserving_order(self):
        assert parse_origins(f"{DASHBOARD},{LOCALHOST},{DASHBOARD}/") == [DASHBOARD, LOCALHOST]


def _client(monkeypatch, origins: str | None) -> TestClient:
    if origins is None:
        monkeypatch.delenv(ORIGINS_ENV_VAR, raising=False)
    else:
        monkeypatch.setenv(ORIGINS_ENV_VAR, origins)
    return TestClient(create_app())


class TestClosedByDefault:
    def test_no_cors_headers_when_unset(self, monkeypatch):
        client = _client(monkeypatch, None)
        response = client.get("/api/v1/health", headers={"Origin": DASHBOARD})

        assert response.status_code == 200
        assert "access-control-allow-origin" not in response.headers

    def test_preflight_is_not_answered_when_unset(self, monkeypatch):
        client = _client(monkeypatch, None)
        response = client.options(
            "/api/v1/economy/items",
            headers={
                "Origin": DASHBOARD,
                "Access-Control-Request-Method": "GET",
            },
        )

        assert "access-control-allow-origin" not in response.headers


class TestConfiguredOrigins:
    def test_allowed_origin_receives_the_header(self, monkeypatch):
        client = _client(monkeypatch, DASHBOARD)
        response = client.get("/api/v1/health", headers={"Origin": DASHBOARD})

        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == DASHBOARD

    def test_unlisted_origin_is_not_granted_access(self, monkeypatch):
        client = _client(monkeypatch, DASHBOARD)
        response = client.get("/api/v1/health", headers={"Origin": "https://evil.example.com"})

        assert response.headers.get("access-control-allow-origin") != "https://evil.example.com"

    def test_preflight_advertises_the_write_endpoint_requirements(self, monkeypatch):
        client = _client(monkeypatch, DASHBOARD)
        response = client.options(
            "/api/v1/economy/events/HeliCrash/toggle-active",
            headers={
                "Origin": DASHBOARD,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "X-API-Key",
            },
        )

        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == DASHBOARD
        assert "POST" in response.headers["access-control-allow-methods"]
        assert "x-api-key" in response.headers["access-control-allow-headers"].lower()

    def test_multiple_origins_are_all_allowed(self, monkeypatch):
        client = _client(monkeypatch, f"{DASHBOARD},{LOCALHOST}")

        for origin in (DASHBOARD, LOCALHOST):
            response = client.get("/api/v1/health", headers={"Origin": origin})
            assert response.headers["access-control-allow-origin"] == origin

    def test_credentials_are_not_allowed(self, monkeypatch):
        """The API authenticates with a static header, not cookies."""
        client = _client(monkeypatch, DASHBOARD)
        response = client.get("/api/v1/health", headers={"Origin": DASHBOARD})

        assert "access-control-allow-credentials" not in response.headers


class TestWildcardRejection:
    def test_wildcard_is_refused_at_startup(self, monkeypatch):
        monkeypatch.setenv(ORIGINS_ENV_VAR, "*")

        with pytest.raises(RuntimeError, match="must list explicit origins"):
            create_app()

    def test_wildcard_mixed_with_real_origins_is_also_refused(self, monkeypatch):
        monkeypatch.setenv(ORIGINS_ENV_VAR, f"{DASHBOARD},*")

        with pytest.raises(RuntimeError, match="must list explicit origins"):
            create_app()
