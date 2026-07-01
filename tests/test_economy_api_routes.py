import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import sentinel_spr019.api.repositories.economy_events_repository as events_repo_module
import sentinel_spr019.api.repositories.economy_items_repository as items_repo_module
import sentinel_spr019.api.security as security_module
from sentinel_spr019.api.main import app


def _apply_schema(db_path: str) -> None:
    root = Path(__file__).resolve().parents[1]
    schema_v1 = root / "sentinel_spr019" / "database" / "schema" / "sentinel_v1_schema.sql"
    schema_v2 = root / "sentinel_spr019" / "database" / "schema" / "sentinel_v1_schema_rev2.sql"
    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema_v1.read_text(encoding="utf-8"))
        conn.executescript(schema_v2.read_text(encoding="utf-8"))


def _seed_api_data(db_path: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            """
            INSERT INTO economy_items (name, nominal, lifetime, restock, min_value, max_value)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                ("Rifle_A", 1, 1000, 100, 0, 1),
                ("Rifle_B", 1, 1000, 100, 0, 1),
                ("Rifle_C", 1, 1000, 100, 0, 1),
                ("Pistol_A", 1, 1000, 100, 0, 1),
            ],
        )
        conn.executemany(
            """
            INSERT INTO economy_events (
                event_name, nominal, min_count, max_count, lifetime, restock,
                saferadius, distanceradius, cleanupradius, position_mode, limit_mode, active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("HeliCrash_A", 1, 1, 1, 100, 10, 1.0, 1.0, 1.0, "fixed", "child", 1),
                ("HeliCrash_B", 1, 1, 1, 100, 10, 1.0, 1.0, 1.0, "fixed", "child", 1),
                ("HeliCrash_C", 1, 1, 1, 100, 10, 1.0, 1.0, 1.0, "fixed", "child", 1),
                ("HeliCrash_Inactive", 1, 1, 1, 100, 10, 1.0, 1.0, 1.0, "fixed", "child", 0),
                ("Police_A", 1, 1, 1, 100, 10, 1.0, 1.0, 1.0, "fixed", "child", 1),
            ],
        )
        conn.commit()


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    db_path = str(tmp_path / "sentinel.db")
    _apply_schema(db_path)
    _seed_api_data(db_path)

    def _connect(_db_path=None):
        return sqlite3.connect(db_path)

    monkeypatch.setattr(items_repo_module, "get_connection", _connect)
    monkeypatch.setattr(events_repo_module, "get_connection", _connect)

    security_module.get_security_settings.cache_clear()
    with TestClient(app) as client:
        yield client
    security_module.get_security_settings.cache_clear()


def test_items_search_reports_full_matching_total(api_client):
    response = api_client.get("/api/v1/economy/items?search=Rifle&limit=2&offset=0")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["data"]) == 2
    assert payload["total"] == 3


def test_events_search_reports_full_matching_total_with_active_filter(api_client):
    response = api_client.get("/api/v1/economy/events?search=HeliCrash&active_only=true&limit=2&offset=0")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["data"]) == 2
    assert payload["total"] == 3


def test_toggle_active_returns_503_when_write_key_not_configured(api_client, monkeypatch):
    monkeypatch.delenv("SENTINEL_WRITE_API_KEY", raising=False)
    security_module.get_security_settings.cache_clear()

    response = api_client.post("/api/v1/economy/events/Police_A/toggle-active")
    assert response.status_code == 503


def test_toggle_active_requires_header_when_write_key_configured(api_client, monkeypatch):
    monkeypatch.setenv("SENTINEL_WRITE_API_KEY", "test-write-key")
    security_module.get_security_settings.cache_clear()

    response = api_client.post("/api/v1/economy/events/Police_A/toggle-active")
    assert response.status_code == 401


def test_toggle_active_rejects_invalid_key(api_client, monkeypatch):
    monkeypatch.setenv("SENTINEL_WRITE_API_KEY", "test-write-key")
    security_module.get_security_settings.cache_clear()

    response = api_client.post(
        "/api/v1/economy/events/Police_A/toggle-active",
        headers={"X-API-Key": "wrong-key"},
    )
    assert response.status_code == 403


def test_toggle_active_accepts_valid_key(api_client, monkeypatch):
    monkeypatch.setenv("SENTINEL_WRITE_API_KEY", "test-write-key")
    security_module.get_security_settings.cache_clear()

    response = api_client.post(
        "/api/v1/economy/events/Police_A/toggle-active",
        headers={"X-API-Key": "test-write-key"},
    )
    assert response.status_code == 200
    assert response.json()["active"] is False


def test_read_events_endpoint_stays_accessible_without_key(api_client, monkeypatch):
    monkeypatch.delenv("SENTINEL_WRITE_API_KEY", raising=False)
    security_module.get_security_settings.cache_clear()

    response = api_client.get("/api/v1/economy/events?limit=1&offset=0")
    assert response.status_code == 200
