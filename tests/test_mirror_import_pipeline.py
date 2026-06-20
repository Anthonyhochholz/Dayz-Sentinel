import sqlite3
import textwrap
from pathlib import Path

from sentinel_spr019.importer.file_classifier import classify_file
from sentinel_spr019.importer.import_pipeline import run_mirror_import


def _apply_schema(db_path: str) -> None:
    root = Path(__file__).resolve().parents[1]
    schema_v1 = root / "sentinel_spr019" / "database" / "schema" / "sentinel_v1_schema.sql"
    schema_v2 = root / "sentinel_spr019" / "database" / "schema" / "sentinel_v1_schema_rev2.sql"
    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema_v1.read_text(encoding="utf-8"))
        conn.executescript(schema_v2.read_text(encoding="utf-8"))


def test_classify_file_rules():
    assert classify_file("types.xml").file_type == "economy_types_xml"
    assert classify_file("events.xml").file_type == "economy_events_xml"
    assert classify_file("cluster.xml").file_type == "xml_other"
    assert classify_file("server.rpt").file_type == "rpt_log"
    assert classify_file("notes.txt").file_type == "unknown"


def test_run_mirror_import_tracks_scan_classification_and_imports(tmp_path):
    mirror_root = tmp_path / "mirror"
    mirror_root.mkdir()
    db = str(tmp_path / "sentinel.db")
    _apply_schema(db)

    (mirror_root / "types.xml").write_text(
        textwrap.dedent(
            """\
            <types>
              <type name="AKM">
                <nominal>3</nominal>
                <lifetime>3600</lifetime>
                <restock>300</restock>
                <quantmin>1</quantmin>
                <quantmax>2</quantmax>
              </type>
            </types>
            """
        ),
        encoding="utf-8",
    )
    (mirror_root / "events.xml").write_text(
        textwrap.dedent(
            """\
            <events>
              <event name="ZmbM_Test">
                <nominal>1</nominal>
                <min>1</min>
                <max>2</max>
                <lifetime>300</lifetime>
                <restock>30</restock>
                <saferadius>10</saferadius>
                <distanceradius>20</distanceradius>
                <cleanupradius>30</cleanupradius>
                <position>fixed</position>
                <limit>child</limit>
                <active>1</active>
              </event>
            </events>
            """
        ),
        encoding="utf-8",
    )
    (mirror_root / "unknown.log").write_text("unclassified", encoding="utf-8")

    summary = run_mirror_import(str(mirror_root), db_file=db)
    assert summary["status"] == "completed"
    assert summary["files_discovered"] == 3
    assert summary["files_imported"] == 2
    assert summary["files_skipped"] == 0
    assert summary["files_unsupported"] == 1
    assert summary["files_failed"] == 0

    with sqlite3.connect(db) as conn:
        scan_status = conn.execute(
            "SELECT status FROM mirror_scans WHERE id = ?",
            (summary["scan_id"],),
        ).fetchone()[0]
        assert scan_status == "completed"

        item_count = conn.execute("SELECT COUNT(*) FROM economy_items WHERE name = 'AKM'").fetchone()[0]
        event_count = conn.execute("SELECT COUNT(*) FROM economy_events WHERE event_name = 'ZmbM_Test'").fetchone()[0]
        assert item_count == 1
        assert event_count == 1

        statuses = [
            row[0]
            for row in conn.execute(
                "SELECT import_status FROM mirror_scan_files WHERE scan_id = ? ORDER BY relative_path ASC",
                (summary["scan_id"],),
            ).fetchall()
        ]
        assert statuses == ["imported", "imported", "unsupported"]

        run_statuses = [row[0] for row in conn.execute("SELECT status FROM import_runs ORDER BY id ASC").fetchall()]
        assert run_statuses == ["completed", "completed"]


def test_run_mirror_import_tracks_failed_imports(tmp_path):
    mirror_root = tmp_path / "mirror"
    mirror_root.mkdir()
    db = str(tmp_path / "sentinel.db")
    _apply_schema(db)

    (mirror_root / "types.xml").write_text(
        textwrap.dedent(
            """\
            <types>
              <type name="M4A1">
                <nominal>2</nominal>
                <lifetime>1200</lifetime>
                <restock>100</restock>
                <quantmin>1</quantmin>
                <quantmax>1</quantmax>
              </type>
            </types>
            """
        ),
        encoding="utf-8",
    )
    (mirror_root / "events.xml").write_text(
        textwrap.dedent(
            """\
            <events>
              <event name="ZmbBroken">
                <nominal>abc</nominal>
                <min>1</min>
                <max>2</max>
                <lifetime>300</lifetime>
                <restock>30</restock>
                <saferadius>10</saferadius>
                <distanceradius>20</distanceradius>
                <cleanupradius>30</cleanupradius>
                <position>fixed</position>
                <limit>child</limit>
                <active>1</active>
              </event>
            </events>
            """
        ),
        encoding="utf-8",
    )

    summary = run_mirror_import(str(mirror_root), db_file=db)
    assert summary["status"] == "completed_with_errors"
    assert summary["files_discovered"] == 2
    assert summary["files_imported"] == 1
    assert summary["files_skipped"] == 0
    assert summary["files_unsupported"] == 0
    assert summary["files_failed"] == 1

    with sqlite3.connect(db) as conn:
        statuses = dict(
            conn.execute(
                "SELECT relative_path, import_status FROM mirror_scan_files WHERE scan_id = ?",
                (summary["scan_id"],),
            ).fetchall()
        )
        assert statuses["types.xml"] == "imported"
        assert statuses["events.xml"] == "failed"

        error_message = conn.execute(
            "SELECT error_message FROM mirror_scan_files WHERE scan_id = ? AND relative_path = 'events.xml'",
            (summary["scan_id"],),
        ).fetchone()[0]
        assert "Invalid integer for field 'nominal'" in error_message

        run_statuses = sorted(row[0] for row in conn.execute("SELECT status FROM import_runs").fetchall())
        assert run_statuses == ["completed", "failed"]


def test_run_mirror_import_is_idempotent_for_repeated_supported_files(tmp_path):
    mirror_root = tmp_path / "mirror"
    mirror_root.mkdir()
    db = str(tmp_path / "sentinel.db")
    _apply_schema(db)

    (mirror_root / "types.xml").write_text(
        textwrap.dedent(
            """\
            <types>
              <type name="SKS">
                <nominal>4</nominal>
                <lifetime>3600</lifetime>
                <restock>300</restock>
                <quantmin>1</quantmin>
                <quantmax>2</quantmax>
              </type>
            </types>
            """
        ),
        encoding="utf-8",
    )
    (mirror_root / "events.xml").write_text(
        textwrap.dedent(
            """\
            <events>
              <event name="ZmbF_Idempotent">
                <nominal>1</nominal>
                <min>1</min>
                <max>2</max>
                <lifetime>300</lifetime>
                <restock>30</restock>
                <saferadius>10</saferadius>
                <distanceradius>20</distanceradius>
                <cleanupradius>30</cleanupradius>
                <position>fixed</position>
                <limit>child</limit>
                <active>1</active>
              </event>
            </events>
            """
        ),
        encoding="utf-8",
    )

    first = run_mirror_import(str(mirror_root), db_file=db)
    second = run_mirror_import(str(mirror_root), db_file=db)

    assert first["status"] == "completed"
    assert first["files_imported"] == 2
    assert first["files_skipped"] == 0
    assert second["status"] == "completed"
    assert second["files_imported"] == 0
    assert second["files_skipped"] == 2
    assert second["files_failed"] == 0

    with sqlite3.connect(db) as conn:
        item_count = conn.execute("SELECT COUNT(*) FROM economy_items WHERE name = 'SKS'").fetchone()[0]
        event_count = conn.execute(
            "SELECT COUNT(*) FROM economy_events WHERE event_name = 'ZmbF_Idempotent'"
        ).fetchone()[0]
        run_count = conn.execute("SELECT COUNT(*) FROM import_runs").fetchone()[0]
        second_scan_statuses = [
            row[0]
            for row in conn.execute(
                "SELECT import_status FROM mirror_scan_files WHERE scan_id = ? ORDER BY relative_path",
                (second["scan_id"],),
            ).fetchall()
        ]

    assert item_count == 1
    assert event_count == 1
    assert run_count == 2
    assert second_scan_statuses == ["skipped", "skipped"]
