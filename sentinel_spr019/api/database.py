import sqlite3
from pathlib import Path


def get_connection():
    db_path = Path(__file__).resolve().parent.parent / "database" / "sqlite" / "sentinel.db"
    return sqlite3.connect(str(db_path))


def dict_factory(cursor, row):
    """Convert database rows to dictionaries."""
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}
