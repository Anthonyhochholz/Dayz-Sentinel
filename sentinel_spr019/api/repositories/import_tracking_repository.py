from datetime import datetime, timezone

from sentinel_spr019.api.database import dict_factory, get_connection


class ImportTrackingRepository:
    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _ensure_schema(conn) -> None:
        cursor = conn.cursor()
        cursor.executescript(
            """
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS import_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_name TEXT NOT NULL UNIQUE,
                source_path TEXT,
                source_type TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS import_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                status TEXT NOT NULL,
                importer_version TEXT,
                source_id INTEGER,
                FOREIGN KEY(source_id) REFERENCES import_sources(id)
            );

            CREATE TABLE IF NOT EXISTS mirror_scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mirror_root TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                status TEXT NOT NULL,
                scanner_version TEXT
            );

            CREATE TABLE IF NOT EXISTS mirror_scan_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id INTEGER NOT NULL,
                source_id INTEGER,
                relative_path TEXT NOT NULL,
                absolute_path TEXT NOT NULL,
                file_size_bytes INTEGER,
                file_type TEXT NOT NULL,
                classifier_reason TEXT,
                is_supported INTEGER NOT NULL DEFAULT 0,
                import_run_id INTEGER,
                import_status TEXT NOT NULL,
                error_message TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(scan_id) REFERENCES mirror_scans(id) ON DELETE CASCADE,
                FOREIGN KEY(source_id) REFERENCES import_sources(id),
                FOREIGN KEY(import_run_id) REFERENCES import_runs(id),
                UNIQUE(scan_id, relative_path)
            );
            """
        )
        conn.commit()

    @staticmethod
    def start_scan(mirror_root: str, scanner_version: str, db_path: str | None = None) -> int:
        conn = get_connection(db_path)
        try:
            ImportTrackingRepository._ensure_schema(conn)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO mirror_scans (mirror_root, started_at, status, scanner_version)
                VALUES (?, ?, ?, ?)
                """,
                (mirror_root, ImportTrackingRepository._now(), "running", scanner_version),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    @staticmethod
    def finish_scan(scan_id: int, status: str, db_path: str | None = None) -> None:
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE mirror_scans
                SET status = ?, finished_at = ?
                WHERE id = ?
                """,
                (status, ImportTrackingRepository._now(), scan_id),
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def get_or_create_source(
        source_name: str,
        source_path: str,
        source_type: str,
        db_path: str | None = None,
    ) -> int:
        conn = get_connection(db_path)
        try:
            ImportTrackingRepository._ensure_schema(conn)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM import_sources WHERE source_name = ?", (source_name,))
            row = cursor.fetchone()
            if row:
                source_id = row[0]
                cursor.execute(
                    """
                    UPDATE import_sources
                    SET source_path = ?, source_type = ?
                    WHERE id = ?
                    """,
                    (source_path, source_type, source_id),
                )
                conn.commit()
                return source_id

            cursor.execute(
                """
                INSERT INTO import_sources (source_name, source_path, source_type)
                VALUES (?, ?, ?)
                """,
                (source_name, source_path, source_type),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    @staticmethod
    def create_import_run(
        source_id: int,
        importer_version: str,
        db_path: str | None = None,
    ) -> int:
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO import_runs (started_at, status, importer_version, source_id)
                VALUES (?, ?, ?, ?)
                """,
                (ImportTrackingRepository._now(), "running", importer_version, source_id),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    @staticmethod
    def finish_import_run(run_id: int, status: str, db_path: str | None = None) -> None:
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE import_runs
                SET status = ?, finished_at = ?
                WHERE id = ?
                """,
                (status, ImportTrackingRepository._now(), run_id),
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def record_scan_file(
        scan_id: int,
        source_id: int,
        relative_path: str,
        absolute_path: str,
        file_size_bytes: int,
        file_type: str,
        classifier_reason: str,
        is_supported: bool,
        import_status: str,
        db_path: str | None = None,
    ) -> int:
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO mirror_scan_files (
                    scan_id, source_id, relative_path, absolute_path, file_size_bytes,
                    file_type, classifier_reason, is_supported, import_status, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    scan_id,
                    source_id,
                    relative_path,
                    absolute_path,
                    file_size_bytes,
                    file_type,
                    classifier_reason,
                    1 if is_supported else 0,
                    import_status,
                    ImportTrackingRepository._now(),
                ),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    @staticmethod
    def attach_import_run(scan_file_id: int, run_id: int, db_path: str | None = None) -> None:
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE mirror_scan_files SET import_run_id = ?, import_status = ? WHERE id = ?",
                (run_id, "running", scan_file_id),
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def update_scan_file_status(
        scan_file_id: int,
        import_status: str,
        error_message: str | None = None,
        db_path: str | None = None,
    ) -> None:
        conn = get_connection(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE mirror_scan_files
                SET import_status = ?, error_message = ?
                WHERE id = ?
                """,
                (import_status, error_message, scan_file_id),
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def list_scans(limit: int, offset: int, db_path: str | None = None) -> list[dict]:
        conn = get_connection(db_path)
        try:
            ImportTrackingRepository._ensure_schema(conn)
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, mirror_root, started_at, finished_at, status, scanner_version
                FROM mirror_scans
                ORDER BY id DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )
            return cursor.fetchall()
        finally:
            conn.close()

    @staticmethod
    def get_scan(scan_id: int, db_path: str | None = None) -> dict | None:
        conn = get_connection(db_path)
        try:
            ImportTrackingRepository._ensure_schema(conn)
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, mirror_root, started_at, finished_at, status, scanner_version
                FROM mirror_scans
                WHERE id = ?
                """,
                (scan_id,),
            )
            return cursor.fetchone()
        finally:
            conn.close()

    @staticmethod
    def list_scan_files(scan_id: int, limit: int, offset: int, db_path: str | None = None) -> list[dict]:
        conn = get_connection(db_path)
        try:
            ImportTrackingRepository._ensure_schema(conn)
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, scan_id, source_id, relative_path, absolute_path, file_size_bytes,
                       file_type, classifier_reason, is_supported, import_run_id, import_status,
                       error_message, created_at
                FROM mirror_scan_files
                WHERE scan_id = ?
                ORDER BY id ASC
                LIMIT ? OFFSET ?
                """,
                (scan_id, limit, offset),
            )
            return cursor.fetchall()
        finally:
            conn.close()

    @staticmethod
    def list_runs(limit: int, offset: int, db_path: str | None = None) -> list[dict]:
        conn = get_connection(db_path)
        try:
            ImportTrackingRepository._ensure_schema(conn)
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT r.id, r.started_at, r.finished_at, r.status, r.importer_version, r.source_id,
                       s.source_name, s.source_path, s.source_type
                FROM import_runs r
                LEFT JOIN import_sources s ON s.id = r.source_id
                ORDER BY r.id DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )
            return cursor.fetchall()
        finally:
            conn.close()
