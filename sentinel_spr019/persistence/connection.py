import os
import sqlite3
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_DB_PATH = str(_PACKAGE_ROOT / "database" / "sqlite" / "sentinel.db")
_SCHEMA_FILES = (
    _PACKAGE_ROOT / "database" / "schema" / "sentinel_v1_schema.sql",
    _PACKAGE_ROOT / "database" / "schema" / "sentinel_v1_schema_rev2.sql",
)


def default_db_path() -> str:
    """Return the default SQLite path used when no path is configured."""
    return _DEFAULT_DB_PATH


def _bootstrap_database(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        return

    with sqlite3.connect(str(db_path)) as conn:
        for schema_file in _SCHEMA_FILES:
            try:
                sql_text = schema_file.read_text(encoding="utf-8")
            except FileNotFoundError as exc:
                raise RuntimeError(f"Schema file not found: {schema_file}") from exc
            except OSError as exc:
                raise RuntimeError(f"Failed to read schema file: {schema_file}") from exc

            try:
                conn.executescript(sql_text)
            except sqlite3.Error as exc:
                raise RuntimeError(f"SQL error in schema file: {schema_file}") from exc
        conn.commit()


def connect(db_path: str | Path) -> sqlite3.Connection:
    """Open a SQLite connection with the project's connection invariants applied.

    `PRAGMA foreign_keys` is a per-connection setting, so the declaration in the
    schema files does not carry over to later connections. Every connection in
    the project is opened through this function so that referential integrity is
    enforced consistently for API reads, writes, and importer runs alike.
    """
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Open a connection to the configured database, bootstrapping it if absent."""
    if db_path is None:
        db_path = os.getenv("SENTINEL_DB_PATH", _DEFAULT_DB_PATH)

    resolved_path = Path(db_path)
    _bootstrap_database(resolved_path)
    return connect(resolved_path)


def dict_factory(cursor, row):
    """Convert database rows to dictionaries."""
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}
