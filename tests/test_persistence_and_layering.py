"""Tests for the shared persistence layer and the importer/API layer boundary."""

import ast
import sqlite3
from pathlib import Path

import pytest

from sentinel_spr019.persistence.connection import (
    connect,
    default_db_path,
    dict_factory,
    get_connection,
)

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "sentinel_spr019"


def _foreign_keys_enabled(conn: sqlite3.Connection) -> bool:
    return bool(conn.execute("PRAGMA foreign_keys").fetchone()[0])


class TestConnectionInvariants:
    def test_connect_enables_foreign_keys(self, tmp_path):
        db_path = tmp_path / "plain.db"
        with connect(db_path) as conn:
            assert _foreign_keys_enabled(conn)

    def test_get_connection_enables_foreign_keys(self, tmp_path):
        with get_connection(tmp_path / "bootstrapped.db") as conn:
            assert _foreign_keys_enabled(conn)

    def test_raw_sqlite3_connect_does_not_enable_foreign_keys(self, tmp_path):
        """Guards the reason connect() exists: the pragma is per-connection.

        PRAGMA foreign_keys in the schema files applies only to the connection
        that ran the script, so it does not carry over to later connections.
        """
        db_path = tmp_path / "raw.db"
        with sqlite3.connect(db_path) as conn:
            assert not _foreign_keys_enabled(conn)

    def test_foreign_key_violation_is_rejected_on_connect(self, tmp_path):
        db_path = tmp_path / "fk.db"
        with connect(db_path) as conn:
            conn.executescript(
                """
                CREATE TABLE parent (id INTEGER PRIMARY KEY);
                CREATE TABLE child (
                    id INTEGER PRIMARY KEY,
                    parent_id INTEGER REFERENCES parent(id)
                );
                """
            )
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute("INSERT INTO child (parent_id) VALUES (999)")


class TestBootstrap:
    def test_get_connection_bootstraps_missing_database(self, tmp_path):
        db_path = tmp_path / "nested" / "sentinel.db"
        assert not db_path.exists()

        with get_connection(db_path) as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }

        assert db_path.exists()
        # One table from each schema file, proving both were applied.
        assert "economy_items" in tables
        assert "mirror_scans" in tables

    def test_get_connection_honours_env_override(self, tmp_path, monkeypatch):
        db_path = tmp_path / "from-env.db"
        monkeypatch.setenv("SENTINEL_DB_PATH", str(db_path))

        with get_connection() as conn:
            conn.execute("SELECT 1")

        assert db_path.exists()

    def test_default_db_path_points_into_the_package(self):
        assert default_db_path().endswith("database/sqlite/sentinel.db")


class TestDictFactory:
    def test_rows_are_returned_as_dicts(self, tmp_path):
        with connect(tmp_path / "rows.db") as conn:
            conn.row_factory = dict_factory
            row = conn.execute("SELECT 1 AS one, 'x' AS letter").fetchone()
        assert row == {"one": 1, "letter": "x"}


def _imported_modules(python_file: Path) -> set[str]:
    tree = ast.parse(python_file.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            modules.add(node.module)
    return modules


class TestLayerBoundaries:
    """ARCH-001: the importer layer must not depend on the API layer."""

    def test_importer_layer_does_not_import_api_layer(self):
        offenders = {}
        for python_file in sorted((PACKAGE_ROOT / "importer").rglob("*.py")):
            api_imports = {
                module
                for module in _imported_modules(python_file)
                if module.startswith("sentinel_spr019.api")
            }
            if api_imports:
                offenders[str(python_file.relative_to(PACKAGE_ROOT))] = sorted(api_imports)

        assert offenders == {}, f"importer modules importing the API layer: {offenders}"

    def test_persistence_layer_is_independent_of_api_and_importer(self):
        offenders = {}
        for python_file in sorted((PACKAGE_ROOT / "persistence").rglob("*.py")):
            upper_imports = {
                module
                for module in _imported_modules(python_file)
                if module.startswith(("sentinel_spr019.api", "sentinel_spr019.importer"))
            }
            if upper_imports:
                offenders[str(python_file.relative_to(PACKAGE_ROOT))] = sorted(upper_imports)

        assert offenders == {}, f"persistence modules depending on upper layers: {offenders}"

    def test_every_importer_module_uses_the_shared_connect_helper(self):
        """No importer may open SQLite directly and bypass the pragma."""
        offenders = []
        for python_file in sorted((PACKAGE_ROOT / "importer").rglob("*.py")):
            source = python_file.read_text(encoding="utf-8")
            if "sqlite3.connect(" in source:
                offenders.append(str(python_file.relative_to(PACKAGE_ROOT)))

        assert offenders == [], f"modules calling sqlite3.connect directly: {offenders}"
