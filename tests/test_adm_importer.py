"""
Tests for sentinel_spr019.importer.logs.adm_importer.

Coverage:
  1. Parser — all event types, header date, missing/partial pos
  2. Importer — data stored in correct tables
  3. Duplicate-import idempotency — re-running the same file creates no extra rows
  4. Pipeline integration — adm_log dispatched via run_mirror_import with hash check
"""
import sqlite3
import textwrap
from pathlib import Path

import pytest

from sentinel_spr019.importer.logs.adm_importer import (
    AdminActionEvent,
    ConnectedEvent,
    DiedEvent,
    DisconnectedEvent,
    KilledEvent,
    compute_file_hash,
    import_adm,
    importer_version_for_hash,
    parse_adm,
)
from sentinel_spr019.importer.file_classifier import classify_file
from sentinel_spr019.importer.import_pipeline import run_mirror_import


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _apply_schema(db_path: str) -> None:
    root = Path(__file__).resolve().parents[1]
    schema_v1 = root / "sentinel_spr019" / "database" / "schema" / "sentinel_v1_schema.sql"
    schema_v2 = root / "sentinel_spr019" / "database" / "schema" / "sentinel_v1_schema_rev2.sql"
    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema_v1.read_text(encoding="utf-8"))
        conn.executescript(schema_v2.read_text(encoding="utf-8"))


def _write_adm(tmp_path, content: str, filename: str = "server.adm") -> Path:
    p = tmp_path / filename
    p.write_text(content, encoding="utf-8")
    return p


SAMPLE_ADM = textwrap.dedent("""\
    AdminLog started on 2024-01-15 at 10:00:00
    10:05:00 | Player "Alice" (id=76561198000000001 pos=<1000.00, 200.00, 3000.00>) is connected
    10:10:00 | Player "Bob" (id=76561198000000002 pos=<2000.00, 300.00, 4000.00>) is connected
    10:30:00 | Player "Alice" (id=76561198000000001 pos=<1001.00, 200.00, 3001.00>) has been disconnected after 1500s
    11:00:00 | Player "Alice" (id=76561198000000001 pos=<1500.00, 250.00, 3500.00>) killed by Player "Bob" (id=76561198000000002 pos=<1502.00, 250.00, 3502.00>) with AK74 from 18.5 meters
    11:30:00 | Player "Bob" (id=76561198000000002 pos=<2100.00, 310.00, 4100.00>) died. Stats> Water: 30.00 Energy: 15.00 Bleed sources: 1
    12:00:00 | Admin "ServerAdmin" (id=76561198999999999): kick Bob reason griefing
""")


# ---------------------------------------------------------------------------
# 1. File classifier
# ---------------------------------------------------------------------------

class TestClassifier:
    def test_adm_extension_lower(self):
        cls = classify_file("server.adm")
        assert cls.file_type == "adm_log"
        assert cls.should_import is True

    def test_adm_extension_upper(self):
        cls = classify_file("SERVER.ADM")
        assert cls.file_type == "adm_log"
        assert cls.should_import is True


# ---------------------------------------------------------------------------
# 2. Parser — event types
# ---------------------------------------------------------------------------

class TestParser:
    def test_header_start_time(self, tmp_path):
        adm = _write_adm(tmp_path, SAMPLE_ADM)
        start_time, _ = parse_adm(adm)
        assert start_time == "2024-01-15 10:00:00"

    def test_connected_event_count(self, tmp_path):
        adm = _write_adm(tmp_path, SAMPLE_ADM)
        _, events = parse_adm(adm)
        connected = [e for e in events if isinstance(e, ConnectedEvent)]
        assert len(connected) == 2

    def test_connected_event_fields(self, tmp_path):
        adm = _write_adm(tmp_path, SAMPLE_ADM)
        _, events = parse_adm(adm)
        alice = next(e for e in events if isinstance(e, ConnectedEvent) and e.player_uid == "76561198000000001")
        assert alice.player_name == "Alice"
        assert alice.timestamp == "2024-01-15 10:05:00"
        assert alice.pos_x == pytest.approx(1000.0)
        assert alice.pos_y == pytest.approx(200.0)
        assert alice.pos_z == pytest.approx(3000.0)

    def test_disconnected_event(self, tmp_path):
        adm = _write_adm(tmp_path, SAMPLE_ADM)
        _, events = parse_adm(adm)
        disconnected = [e for e in events if isinstance(e, DisconnectedEvent)]
        assert len(disconnected) == 1
        assert disconnected[0].player_uid == "76561198000000001"
        assert disconnected[0].timestamp == "2024-01-15 10:30:00"

    def test_killed_event_fields(self, tmp_path):
        adm = _write_adm(tmp_path, SAMPLE_ADM)
        _, events = parse_adm(adm)
        kills = [e for e in events if isinstance(e, KilledEvent)]
        assert len(kills) == 1
        k = kills[0]
        assert k.victim_uid == "76561198000000001"
        assert k.victim_name == "Alice"
        assert k.killer_uid == "76561198000000002"
        assert k.killer_name == "Bob"
        assert k.weapon == "AK74"
        assert k.distance == pytest.approx(18.5)
        assert k.victim_pos_x == pytest.approx(1500.0)

    def test_died_event(self, tmp_path):
        adm = _write_adm(tmp_path, SAMPLE_ADM)
        _, events = parse_adm(adm)
        died = [e for e in events if isinstance(e, DiedEvent)]
        assert len(died) == 1
        assert died[0].player_uid == "76561198000000002"
        assert died[0].player_name == "Bob"

    def test_admin_action_event(self, tmp_path):
        adm = _write_adm(tmp_path, SAMPLE_ADM)
        _, events = parse_adm(adm)
        admins = [e for e in events if isinstance(e, AdminActionEvent)]
        assert len(admins) == 1
        a = admins[0]
        assert a.admin_name == "ServerAdmin"
        assert a.admin_uid == "76561198999999999"
        assert "kick" in a.action_text.lower()

    def test_no_header_uses_time_only(self, tmp_path):
        content = "10:00:00 | Player \"X\" (id=111 pos=<0.0, 0.0, 0.0>) is connected\n"
        adm = _write_adm(tmp_path, content)
        start_time, events = parse_adm(adm)
        assert start_time == ""
        assert len(events) == 1
        assert events[0].timestamp == "10:00:00"

    def test_pos_optional_in_disconnected(self, tmp_path):
        content = textwrap.dedent("""\
            AdminLog started on 2024-02-01 at 09:00:00
            09:05:00 | Player "NoPosPlayer" (id=999) has been disconnected
        """)
        adm = _write_adm(tmp_path, content)
        _, events = parse_adm(adm)
        disconnected = [e for e in events if isinstance(e, DisconnectedEvent)]
        assert len(disconnected) == 1
        assert disconnected[0].pos_x is None

    def test_unknown_lines_skipped(self, tmp_path):
        content = textwrap.dedent("""\
            AdminLog started on 2024-02-01 at 08:00:00
            08:01:00 | Some unknown log message here
            08:02:00 | Player "P" (id=1 pos=<0.0, 0.0, 0.0>) is connected
        """)
        adm = _write_adm(tmp_path, content)
        _, events = parse_adm(adm)
        assert len(events) == 1
        assert isinstance(events[0], ConnectedEvent)

    def test_total_event_count(self, tmp_path):
        adm = _write_adm(tmp_path, SAMPLE_ADM)
        _, events = parse_adm(adm)
        # 2 connected, 1 disconnected, 1 killed, 1 died, 1 admin = 6
        assert len(events) == 6


# ---------------------------------------------------------------------------
# 3. Importer — data written to DB tables
# ---------------------------------------------------------------------------

class TestImporter:
    def test_players_created(self, tmp_path):
        db = str(tmp_path / "sentinel.db")
        _apply_schema(db)
        adm = _write_adm(tmp_path, SAMPLE_ADM)

        import_adm(str(adm), db)

        with sqlite3.connect(db) as conn:
            count = conn.execute("SELECT COUNT(*) FROM players").fetchone()[0]
        # Alice, Bob, ServerAdmin
        assert count == 3

    def test_player_session_connect_time(self, tmp_path):
        db = str(tmp_path / "sentinel.db")
        _apply_schema(db)
        adm = _write_adm(tmp_path, SAMPLE_ADM)

        import_adm(str(adm), db)

        with sqlite3.connect(db) as conn:
            alice_id = conn.execute(
                "SELECT id FROM players WHERE player_uid = '76561198000000001'"
            ).fetchone()[0]
            session = conn.execute(
                "SELECT connect_time, disconnect_time FROM player_sessions WHERE player_id = ?",
                (alice_id,),
            ).fetchone()

        assert session is not None
        assert session[0] == "2024-01-15 10:05:00"
        assert session[1] == "2024-01-15 10:30:00"

    def test_kill_creates_damage_event(self, tmp_path):
        db = str(tmp_path / "sentinel.db")
        _apply_schema(db)
        adm = _write_adm(tmp_path, SAMPLE_ADM)

        import_adm(str(adm), db)

        with sqlite3.connect(db) as conn:
            alice_id = conn.execute(
                "SELECT id FROM players WHERE player_uid = '76561198000000001'"
            ).fetchone()[0]
            row = conn.execute(
                "SELECT weapon, source FROM player_damage_events WHERE player_id = ?",
                (alice_id,),
            ).fetchone()

        assert row is not None
        assert row[0] == "AK74"
        assert row[1] == "76561198000000002"

    def test_died_creates_player_action(self, tmp_path):
        db = str(tmp_path / "sentinel.db")
        _apply_schema(db)
        adm = _write_adm(tmp_path, SAMPLE_ADM)

        import_adm(str(adm), db)

        with sqlite3.connect(db) as conn:
            bob_id = conn.execute(
                "SELECT id FROM players WHERE player_uid = '76561198000000002'"
            ).fetchone()[0]
            row = conn.execute(
                "SELECT action_name FROM player_actions WHERE player_id = ? AND action_name = 'died'",
                (bob_id,),
            ).fetchone()

        assert row is not None

    def test_admin_action_stored(self, tmp_path):
        db = str(tmp_path / "sentinel.db")
        _apply_schema(db)
        adm = _write_adm(tmp_path, SAMPLE_ADM)

        import_adm(str(adm), db)

        with sqlite3.connect(db) as conn:
            admin_id = conn.execute(
                "SELECT id FROM players WHERE player_uid = '76561198999999999'"
            ).fetchone()[0]
            row = conn.execute(
                "SELECT action_name, item_name FROM player_actions WHERE player_id = ?",
                (admin_id,),
            ).fetchone()

        assert row is not None
        assert row[0] == "admin_action"
        assert "kick" in row[1].lower()

    def test_server_session_created(self, tmp_path):
        db = str(tmp_path / "sentinel.db")
        _apply_schema(db)
        adm = _write_adm(tmp_path, SAMPLE_ADM)

        import_adm(str(adm), db)

        with sqlite3.connect(db) as conn:
            row = conn.execute(
                "SELECT start_time, executable FROM server_sessions WHERE executable = 'adm_log'"
            ).fetchone()

        assert row is not None
        assert row[0] == "2024-01-15 10:00:00"

    def test_returns_stored_and_skipped_counts(self, tmp_path):
        db = str(tmp_path / "sentinel.db")
        _apply_schema(db)
        adm = _write_adm(tmp_path, SAMPLE_ADM)

        stored, skipped = import_adm(str(adm), db)

        assert stored > 0
        assert isinstance(skipped, int)


# ---------------------------------------------------------------------------
# 4. Idempotency — duplicate imports create no extra rows
# ---------------------------------------------------------------------------

class TestIdempotency:
    def test_reimport_same_file_no_duplicate_players(self, tmp_path):
        db = str(tmp_path / "sentinel.db")
        _apply_schema(db)
        adm = _write_adm(tmp_path, SAMPLE_ADM)

        import_adm(str(adm), db)
        import_adm(str(adm), db)

        with sqlite3.connect(db) as conn:
            count = conn.execute("SELECT COUNT(*) FROM players").fetchone()[0]
        assert count == 3

    def test_reimport_same_file_no_duplicate_sessions(self, tmp_path):
        db = str(tmp_path / "sentinel.db")
        _apply_schema(db)
        adm = _write_adm(tmp_path, SAMPLE_ADM)

        import_adm(str(adm), db)
        import_adm(str(adm), db)

        with sqlite3.connect(db) as conn:
            count = conn.execute("SELECT COUNT(*) FROM player_sessions").fetchone()[0]
        assert count == 2  # Alice and Bob each have one session

    def test_reimport_same_file_no_duplicate_damage_events(self, tmp_path):
        db = str(tmp_path / "sentinel.db")
        _apply_schema(db)
        adm = _write_adm(tmp_path, SAMPLE_ADM)

        import_adm(str(adm), db)
        import_adm(str(adm), db)

        with sqlite3.connect(db) as conn:
            count = conn.execute("SELECT COUNT(*) FROM player_damage_events").fetchone()[0]
        assert count == 1

    def test_reimport_same_file_no_duplicate_actions(self, tmp_path):
        db = str(tmp_path / "sentinel.db")
        _apply_schema(db)
        adm = _write_adm(tmp_path, SAMPLE_ADM)

        import_adm(str(adm), db)
        import_adm(str(adm), db)

        with sqlite3.connect(db) as conn:
            first_count = conn.execute("SELECT COUNT(*) FROM player_actions").fetchone()[0]

        import_adm(str(adm), db)

        with sqlite3.connect(db) as conn:
            count_after_third = conn.execute("SELECT COUNT(*) FROM player_actions").fetchone()[0]

        assert count_after_third == first_count

    def test_second_import_returns_zero_stored(self, tmp_path):
        db = str(tmp_path / "sentinel.db")
        _apply_schema(db)
        adm = _write_adm(tmp_path, SAMPLE_ADM)

        import_adm(str(adm), db)
        stored, _ = import_adm(str(adm), db)

        # All data already present: zero new rows
        assert stored == 0

    def test_server_session_not_duplicated(self, tmp_path):
        db = str(tmp_path / "sentinel.db")
        _apply_schema(db)
        adm = _write_adm(tmp_path, SAMPLE_ADM)

        import_adm(str(adm), db)
        import_adm(str(adm), db)

        with sqlite3.connect(db) as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM server_sessions WHERE executable = 'adm_log'"
            ).fetchone()[0]
        assert count == 1


# ---------------------------------------------------------------------------
# 5. File hash utilities
# ---------------------------------------------------------------------------

class TestFileHash:
    def test_hash_is_hex_string(self, tmp_path):
        adm = _write_adm(tmp_path, SAMPLE_ADM)
        h = compute_file_hash(str(adm))
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_same_content_same_hash(self, tmp_path):
        a = _write_adm(tmp_path, SAMPLE_ADM, "a.adm")
        b = _write_adm(tmp_path, SAMPLE_ADM, "b.adm")
        assert compute_file_hash(str(a)) == compute_file_hash(str(b))

    def test_different_content_different_hash(self, tmp_path):
        a = _write_adm(tmp_path, SAMPLE_ADM, "a.adm")
        b = _write_adm(tmp_path, SAMPLE_ADM + "\n# extra", "b.adm")
        assert compute_file_hash(str(a)) != compute_file_hash(str(b))

    def test_importer_version_format(self, tmp_path):
        adm = _write_adm(tmp_path, SAMPLE_ADM)
        h = compute_file_hash(str(adm))
        version = importer_version_for_hash(h)
        assert version.startswith("adm-importer-v1:sha256=")
        assert version.endswith(h)


# ---------------------------------------------------------------------------
# 6. Pipeline integration
# ---------------------------------------------------------------------------

class TestPipelineIntegration:
    def test_adm_file_dispatched_by_pipeline(self, tmp_path):
        mirror_root = tmp_path / "mirror"
        mirror_root.mkdir()
        db = str(tmp_path / "sentinel.db")
        _apply_schema(db)

        (mirror_root / "server.adm").write_text(SAMPLE_ADM, encoding="utf-8")

        summary = run_mirror_import(str(mirror_root), db_file=db)

        assert summary["status"] == "completed"
        assert summary["files_imported"] == 1
        assert summary["files_failed"] == 0

        with sqlite3.connect(db) as conn:
            player_count = conn.execute("SELECT COUNT(*) FROM players").fetchone()[0]
        assert player_count == 3

    def test_pipeline_skips_adm_on_second_scan_same_content(self, tmp_path):
        mirror_root = tmp_path / "mirror"
        mirror_root.mkdir()
        db = str(tmp_path / "sentinel.db")
        _apply_schema(db)

        (mirror_root / "server.adm").write_text(SAMPLE_ADM, encoding="utf-8")

        run_mirror_import(str(mirror_root), db_file=db)
        summary2 = run_mirror_import(str(mirror_root), db_file=db)

        # Second scan: file hash matches completed run → counts as already imported
        assert summary2["files_imported"] == 1
        assert summary2["files_failed"] == 0

        with sqlite3.connect(db) as conn:
            player_count = conn.execute("SELECT COUNT(*) FROM players").fetchone()[0]
        assert player_count == 3

    def test_pipeline_reimports_adm_when_content_changes(self, tmp_path):
        mirror_root = tmp_path / "mirror"
        mirror_root.mkdir()
        db = str(tmp_path / "sentinel.db")
        _apply_schema(db)

        adm_path = mirror_root / "server.adm"
        adm_path.write_text(SAMPLE_ADM, encoding="utf-8")
        run_mirror_import(str(mirror_root), db_file=db)

        # Append a new player connection to simulate file growth
        extra = textwrap.dedent("""\
            13:00:00 | Player "Charlie" (id=76561198111111111 pos=<500.00, 100.00, 800.00>) is connected
        """)
        adm_path.write_text(SAMPLE_ADM + extra, encoding="utf-8")
        run_mirror_import(str(mirror_root), db_file=db)

        with sqlite3.connect(db) as conn:
            player_count = conn.execute("SELECT COUNT(*) FROM players").fetchone()[0]
        # Charlie is new; Alice, Bob, ServerAdmin already existed
        assert player_count == 4

    def test_pipeline_adm_import_run_records_hash_version(self, tmp_path):
        mirror_root = tmp_path / "mirror"
        mirror_root.mkdir()
        db = str(tmp_path / "sentinel.db")
        _apply_schema(db)

        adm_path = mirror_root / "server.adm"
        adm_path.write_text(SAMPLE_ADM, encoding="utf-8")
        run_mirror_import(str(mirror_root), db_file=db)

        file_hash = compute_file_hash(str(adm_path))
        expected_version = importer_version_for_hash(file_hash)

        with sqlite3.connect(db) as conn:
            row = conn.execute(
                "SELECT importer_version FROM import_runs WHERE status = 'completed'"
            ).fetchone()

        assert row is not None
        assert row[0] == expected_version
