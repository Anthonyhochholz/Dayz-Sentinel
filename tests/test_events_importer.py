import sqlite3
import textwrap
from pathlib import Path

from sentinel_spr019.importer.economy.events_importer import import_events


def _apply_schema(db_path: str) -> None:
    schema_path = Path(__file__).resolve().parents[1] / "sentinel_spr019" / "database" / "schema" / "sentinel_v1_schema.sql"
    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema_path.read_text(encoding="utf-8"))


def _write_events_xml(tmp_path, content: str) -> str:
    path = tmp_path / "events.xml"
    path.write_text(content, encoding="utf-8")
    return str(path)


def test_import_events_is_idempotent_and_updates_existing_rows(tmp_path):
    db = str(tmp_path / "sentinel.db")
    _apply_schema(db)

    xml_v1 = _write_events_xml(
        tmp_path,
        textwrap.dedent(
            """\
            <events>
              <event name="ZmbF_Test">
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
    )
    inserted, updated, skipped = import_events(xml_v1, db)
    assert inserted == 1
    assert updated == 0
    assert skipped == 0

    xml_v2 = _write_events_xml(
        tmp_path,
        textwrap.dedent(
            """\
            <events>
              <event name="ZmbF_Test">
                <nominal>5</nominal>
                <min>2</min>
                <max>6</max>
                <lifetime>900</lifetime>
                <restock>120</restock>
                <saferadius>11</saferadius>
                <distanceradius>22</distanceradius>
                <cleanupradius>33</cleanupradius>
                <position>dynamic</position>
                <limit>mixed</limit>
                <active>0</active>
              </event>
            </events>
            """
        ),
    )
    inserted, updated, skipped = import_events(xml_v2, db)
    assert inserted == 0
    assert updated == 1
    assert skipped == 0

    with sqlite3.connect(db) as conn:
        row_count = conn.execute("SELECT COUNT(*) FROM economy_events WHERE event_name = 'ZmbF_Test'").fetchone()[0]
        row = conn.execute(
            """
            SELECT nominal, min_count, max_count, lifetime, restock, position_mode, limit_mode, active
            FROM economy_events
            WHERE event_name = 'ZmbF_Test'
            """
        ).fetchone()

    assert row_count == 1
    assert row == (5, 2, 6, 900, 120, "dynamic", "mixed", 0)
