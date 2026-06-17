import sqlite3
from pathlib import Path

def get_connection():
    db_path = Path(__file__).resolve().parent.parent / "database" / "sqlite" / "sentinel.db"
    return sqlite3.connect(str(db_path))
