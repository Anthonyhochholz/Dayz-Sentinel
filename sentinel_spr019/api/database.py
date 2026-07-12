import sqlite3
import os
from pathlib import Path

_DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "database" / "sqlite" / "sentinel.db"
_SCHEMA_FILES = (
    Path(__file__).resolve().parent.parent / "database" / "schema" / "sentinel_v1_schema.sql",
    Path(__file__).resolve().parent.parent / "database" / "schema" / "sentinel_v1_schema_rev2.sql",
)


def _bootstrap_database(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        return

    conn = sqlite3.connect(str(db_path))
    try:
        for schema_file in _SCHEMA_FILES:
            conn.executescript(schema_file.read_text(encoding="utf-8"))
        conn.commit()
    finally:
        conn.close()


def get_connection(db_path: str | Path | None = None):
    if db_path is None:
        db_path = os.getenv("SENTINEL_DB_PATH", str(_DEFAULT_DB_PATH))

    resolved_path = Path(db_path)
    _bootstrap_database(resolved_path)
    return sqlite3.connect(str(resolved_path))


def dict_factory(cursor, row):
    """Convert database rows to dictionaries."""
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}
