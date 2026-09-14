"""Contract tests for the read endpoints and their typed response models.

tests/test_economy_api_routes.py covers the security behaviour of the write
endpoint and the search-total regressions. This module covers the response
shapes the endpoints promise via `response_model`, plus the endpoints that
previously had no coverage at all (health, item reads, count endpoints and the
whole import-tracking surface).
"""

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import sentinel_spr019.api.repositories.economy_events_repository as events_repo_module
import sentinel_spr019.api.repositories.economy_items_repository as items_repo_module
import sentinel_spr019.persistence.import_tracking_repository as tracking_repo_module
from sentinel_spr019.api.main import app
from sentinel_spr019.persistence.connection import connect

SCHEMA_DIR = Path(__file__).resolve().parents[1] / "sentinel_spr019" / "database" / "schema"


def _apply_schema(db_path: str) -> None:
    with connect(db_path) as conn:
        for schema_file in ("sentinel_v1_schema.sql", "sentinel_v1_schema_rev2.sql"):
            conn.executescript((SCHEMA_DIR / schema_file).read_text(encoding="utf-8"))
        conn.commit()


def _seed(db_path: str) -> None:
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO economy_items (name, nominal, lifetime, restock, min_value, max_value)
            VALUES ('AKM', 12, 7200, 1800, 2, 5)
            """
        )
        # A deliberately sparse row: types.xml need not declare every field, and
        # the response model has to tolerate the resulting NULLs.
        conn.execute("INSERT INTO economy_items (name) VALUES ('SparseItem')")
        conn.execute(
            """
            INSERT INTO economy_events (
                event_name, nominal, min_count, max_count, lifetime, restock,
                saferadius, distanceradius, cleanupradius, position_mode, limit_mode, active
            ) VALUES ('HeliCrash', 3, 1, 4, 900, 0, 500.0, 100.0, 50.5, 'fixed', 'child', 1)
            """
        )
        conn.execute(
            """
            INSERT INTO economy_events (event_name, active) VALUES ('InactiveEvent', 0)
            """
        )
        conn.execute("INSERT INTO economy_events (event_name) VALUES ('NullActiveEvent')")
        conn.commit()


def _seed_tracking(db_path: str) -> None:
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO import_sources (id, source_name, source_path, source_type)
            VALUES (1, 'db/types.xml', '/mirror/db/types.xml', 'economy_types_xml')
            """
        )
        conn.execute(
            """
            INSERT INTO import_runs (id, started_at, finished_at, status, importer_version, source_id)
            VALUES (1, '2026-09-01T10:00:00+00:00', '2026-09-01T10:00:05+00:00', 'completed', 'v1', 1)
            """
        )
        conn.execute(
            """
            INSERT INTO mirror_scans (id, mirror_root, started_at, finished_at, status, scanner_version)
            VALUES (1, '/mirror', '2026-09-01T10:00:00+00:00', '2026-09-01T10:00:06+00:00', 'completed', 'mirror-scanner-v1')
            """
        )
        conn.execute(
            """
            INSERT INTO mirror_scan_files (
                id, scan_id, source_id, relative_path, absolute_path, file_size_bytes,
                file_type, classifier_reason, is_supported, import_run_id, import_status,
                error_message, created_at
            ) VALUES (
                1, 1, 1, 'db/types.xml', '/mirror/db/types.xml', 2048,
                'economy_types_xml', 'filename matches types.xml', 1, 1, 'imported',
                NULL, '2026-09-01T10:00:01+00:00'
            )
            """
        )
        conn.execute(
            """
            INSERT INTO mirror_scan_files (
                id, scan_id, source_id, relative_path, absolute_path, file_size_bytes,
                file_type, classifier_reason, is_supported, import_run_id, import_status,
                error_message, created_at
            ) VALUES (
                2, 1, NULL, 'server.rpt', '/mirror/server.rpt', 512,
                'rpt_log', 'rpt log support is planned but not implemented', 0, NULL,
                'unsupported', NULL, '2026-09-01T10:00:02+00:00'
            )
            """
        )
        conn.commit()


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = str(tmp_path / "sentinel.db")
    _apply_schema(db_path)
    _seed(db_path)
    _seed_tracking(db_path)

    def _connect(_db_path=None):
        return connect(db_path)

    monkeypatch.setattr(items_repo_module, "get_connection", _connect)
    monkeypatch.setattr(events_repo_module, "get_connection", _connect)
    monkeypatch.setattr(tracking_repo_module, "get_connection", _connect)

    with TestClient(app) as test_client:
        yield test_client


class TestHealth:
    def test_health_returns_ok(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestEconomyItems:
    def test_list_returns_uniform_envelope(self, client):
        response = client.get("/api/v1/economy/items")
        assert response.status_code == 200
        payload = response.json()
        assert set(payload) == {"data", "total", "limit", "offset", "search"}
        assert payload["total"] == 2
        assert payload["limit"] == 50
        assert payload["offset"] == 0
        assert payload["search"] is None

    def test_list_echoes_search_filter(self, client):
        response = client.get("/api/v1/economy/items?search=AK")
        assert response.status_code == 200
        payload = response.json()
        assert payload["search"] == "AK"
        assert [item["name"] for item in payload["data"]] == ["AKM"]

    def test_item_fields_are_typed(self, client):
        response = client.get("/api/v1/economy/items/AKM")
        assert response.status_code == 200
        assert response.json() == {
            "name": "AKM",
            "nominal": 12,
            "min_value": 2,
            "max_value": 5,
            "restock": 1800,
            "lifetime": 7200,
        }

    def test_sparse_row_serialises_nulls_instead_of_failing(self, client):
        """A row with only a name must not trip response validation."""
        response = client.get("/api/v1/economy/items/SparseItem")
        assert response.status_code == 200
        assert response.json() == {
            "name": "SparseItem",
            "nominal": None,
            "min_value": None,
            "max_value": None,
            "restock": None,
            "lifetime": None,
        }

    def test_unknown_item_returns_404(self, client):
        response = client.get("/api/v1/economy/items/DoesNotExist")
        assert response.status_code == 404
        assert "DoesNotExist" in response.json()["detail"]

    def test_count_endpoint(self, client):
        response = client.get("/api/v1/economy/items/stats/count")
        assert response.status_code == 200
        assert response.json() == {"total": 2}

    @pytest.mark.parametrize(
        "query",
        ["limit=0", "limit=1001", "offset=-1"],
    )
    def test_pagination_bounds_are_enforced(self, client, query):
        response = client.get(f"/api/v1/economy/items?{query}")
        assert response.status_code == 422

    def test_pagination_slices_the_collection(self, client):
        first = client.get("/api/v1/economy/items?limit=1&offset=0").json()
        second = client.get("/api/v1/economy/items?limit=1&offset=1").json()
        assert first["total"] == second["total"] == 2
        assert len(first["data"]) == len(second["data"]) == 1
        assert first["data"][0]["name"] != second["data"][0]["name"]


class TestEconomyEvents:
    def test_list_returns_uniform_envelope(self, client):
        response = client.get("/api/v1/economy/events")
        assert response.status_code == 200
        payload = response.json()
        assert set(payload) == {"data", "total", "limit", "offset", "active_only", "search"}
        assert payload["total"] == 3
        assert payload["active_only"] is False
        assert payload["search"] is None

    def test_active_flag_is_serialised_as_boolean(self, client):
        """The stored column is an INTEGER; the contract is a boolean."""
        response = client.get("/api/v1/economy/events/HeliCrash")
        assert response.status_code == 200
        assert response.json()["active"] is True

        response = client.get("/api/v1/economy/events/InactiveEvent")
        assert response.status_code == 200
        assert response.json()["active"] is False

    def test_null_active_flag_is_serialised_as_null(self, client):
        response = client.get("/api/v1/economy/events/NullActiveEvent")
        assert response.status_code == 200
        assert response.json()["active"] is None

    def test_event_fields_are_typed(self, client):
        response = client.get("/api/v1/economy/events/HeliCrash")
        assert response.status_code == 200
        assert response.json() == {
            "event_name": "HeliCrash",
            "nominal": 3,
            "min_count": 1,
            "max_count": 4,
            "lifetime": 900,
            "restock": 0,
            "saferadius": 500.0,
            "distanceradius": 100.0,
            "cleanupradius": 50.5,
            "position_mode": "fixed",
            "limit_mode": "child",
            "active": True,
        }

    def test_active_only_filter(self, client):
        payload = client.get("/api/v1/economy/events?active_only=true").json()
        assert payload["active_only"] is True
        assert [event["event_name"] for event in payload["data"]] == ["HeliCrash"]

    def test_unknown_event_returns_404(self, client):
        response = client.get("/api/v1/economy/events/DoesNotExist")
        assert response.status_code == 404

    def test_count_endpoints(self, client):
        assert client.get("/api/v1/economy/events/stats/count").json() == {
            "total": 3,
            "active_only": False,
        }
        assert client.get("/api/v1/economy/events/stats/count?active_only=true").json() == {
            "total": 1,
            "active_only": True,
        }

    def test_stats_count_is_not_shadowed_by_the_name_route(self, client):
        """`/events/stats/count` must not be read as an event named 'stats'."""
        response = client.get("/api/v1/economy/events/stats/count")
        assert response.status_code == 200
        assert "total" in response.json()


class TestToggleActiveEdgeCases:
    def test_toggling_a_null_active_flag_activates_the_event(self, client, monkeypatch):
        """A NULL flag used to raise TypeError on `1 - None` and surface as 500."""
        import sentinel_spr019.api.security as security_module

        monkeypatch.setenv("SENTINEL_WRITE_API_KEY", "test-key")
        security_module.get_security_settings.cache_clear()
        try:
            response = client.post(
                "/api/v1/economy/events/NullActiveEvent/toggle-active",
                headers={"X-API-Key": "test-key"},
            )
            assert response.status_code == 200
            assert response.json() == {
                "event_name": "NullActiveEvent",
                "active": True,
                "message": "Event set to active",
            }
            assert client.get("/api/v1/economy/events/NullActiveEvent").json()["active"] is True
        finally:
            security_module.get_security_settings.cache_clear()


class TestImportTracking:
    def test_list_scans(self, client):
        response = client.get("/api/v1/import-tracking/scans")
        assert response.status_code == 200
        payload = response.json()
        assert set(payload) == {"data", "limit", "offset"}
        assert payload["data"] == [
            {
                "id": 1,
                "mirror_root": "/mirror",
                "started_at": "2026-09-01T10:00:00+00:00",
                "finished_at": "2026-09-01T10:00:06+00:00",
                "status": "completed",
                "scanner_version": "mirror-scanner-v1",
            }
        ]

    def test_get_scan(self, client):
        response = client.get("/api/v1/import-tracking/scans/1")
        assert response.status_code == 200
        assert response.json()["mirror_root"] == "/mirror"

    def test_unknown_scan_returns_404(self, client):
        response = client.get("/api/v1/import-tracking/scans/999")
        assert response.status_code == 404
        assert "999" in response.json()["detail"]

    def test_non_numeric_scan_id_returns_422(self, client):
        response = client.get("/api/v1/import-tracking/scans/not-a-number")
        assert response.status_code == 422

    def test_list_scan_files_serialises_support_flag_as_boolean(self, client):
        response = client.get("/api/v1/import-tracking/scans/1/files")
        assert response.status_code == 200
        payload = response.json()
        assert payload["scan_id"] == 1
        by_path = {entry["relative_path"]: entry for entry in payload["data"]}
        assert by_path["db/types.xml"]["is_supported"] is True
        assert by_path["db/types.xml"]["import_status"] == "imported"
        assert by_path["server.rpt"]["is_supported"] is False
        assert by_path["server.rpt"]["import_status"] == "unsupported"
        assert by_path["server.rpt"]["source_id"] is None

    def test_scan_files_of_unknown_scan_return_an_empty_page(self, client):
        response = client.get("/api/v1/import-tracking/scans/999/files")
        assert response.status_code == 200
        assert response.json()["data"] == []

    def test_list_runs_joins_the_source(self, client):
        response = client.get("/api/v1/import-tracking/runs")
        assert response.status_code == 200
        run = response.json()["data"][0]
        assert run["status"] == "completed"
        assert run["source_name"] == "db/types.xml"
        assert run["source_type"] == "economy_types_xml"


class TestOpenApiContract:
    def test_no_endpoint_falls_back_to_an_untyped_object(self, client):
        """Guards P1-004: every 200 response must name a schema component."""
        schema = client.get("/openapi.json").json()
        untyped = []
        for path, operations in schema["paths"].items():
            for method, operation in operations.items():
                success = operation.get("responses", {}).get("200")
                if not success:
                    continue
                content = success.get("content", {}).get("application/json", {})
                if "$ref" not in content.get("schema", {}):
                    untyped.append(f"{method.upper()} {path}")

        assert untyped == [], f"endpoints without a typed response model: {untyped}"

    def test_documented_endpoints_are_all_registered(self, client):
        schema = client.get("/openapi.json").json()
        assert set(schema["paths"]) == {
            "/api/v1/health",
            "/api/v1/economy/items",
            "/api/v1/economy/items/{item_name}",
            "/api/v1/economy/items/stats/count",
            "/api/v1/economy/events",
            "/api/v1/economy/events/{event_name}",
            "/api/v1/economy/events/{event_name}/toggle-active",
            "/api/v1/economy/events/stats/count",
            "/api/v1/import-tracking/scans",
            "/api/v1/import-tracking/scans/{scan_id}",
            "/api/v1/import-tracking/scans/{scan_id}/files",
            "/api/v1/import-tracking/runs",
        }
