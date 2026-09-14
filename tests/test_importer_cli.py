"""Tests for the mirror-import command-line entry point."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from sentinel_spr019.importer.cli import EXIT_IMPORT_ERRORS, EXIT_OK, EXIT_USAGE, main

REPO_ROOT = Path(__file__).resolve().parents[1]

_TYPES_XML = """<?xml version="1.0" encoding="UTF-8"?>
<types>
    <type name="AKM">
        <nominal>12</nominal>
        <lifetime>7200</lifetime>
        <restock>1800</restock>
        <min>2</min>
        <max>5</max>
    </type>
</types>
"""

_EVENTS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<events>
    <event name="HeliCrash">
        <nominal>3</nominal>
        <min>1</min>
        <max>4</max>
        <lifetime>900</lifetime>
        <restock>0</restock>
        <saferadius>500</saferadius>
        <distanceradius>100</distanceradius>
        <cleanupradius>50</cleanupradius>
        <position>fixed</position>
        <limit>child</limit>
        <active>1</active>
    </event>
</events>
"""


@pytest.fixture
def mirror(tmp_path):
    root = tmp_path / "mirror"
    (root / "db").mkdir(parents=True)
    (root / "db" / "types.xml").write_text(_TYPES_XML, encoding="utf-8")
    (root / "db" / "events.xml").write_text(_EVENTS_XML, encoding="utf-8")
    (root / "server.rpt").write_text("unsupported for now\n", encoding="utf-8")
    return root


class TestSuccessfulRun:
    def test_reports_a_summary_and_exits_zero(self, mirror, tmp_path, capsys):
        db_path = tmp_path / "cli.db"
        exit_code = main([str(mirror), "--db-path", str(db_path)])

        assert exit_code == EXIT_OK
        out = capsys.readouterr().out
        assert "Mirror import completed" in out
        assert "imported:" in out
        assert str(db_path) in out
        assert db_path.exists()

    def test_json_output_is_machine_readable(self, mirror, tmp_path, capsys):
        db_path = tmp_path / "cli.db"
        assert main([str(mirror), "--db-path", str(db_path), "--json"]) == EXIT_OK

        summary = json.loads(capsys.readouterr().out)
        assert summary["status"] == "completed"
        assert summary["files_discovered"] == 3
        assert summary["files_imported"] == 2
        assert summary["files_unsupported"] == 1
        assert summary["files_failed"] == 0
        assert summary["db_path"] == str(db_path)

    def test_rerun_skips_unchanged_files(self, mirror, tmp_path, capsys):
        db_path = tmp_path / "cli.db"
        main([str(mirror), "--db-path", str(db_path), "--json"])
        capsys.readouterr()

        assert main([str(mirror), "--db-path", str(db_path), "--json"]) == EXIT_OK
        summary = json.loads(capsys.readouterr().out)
        assert summary["files_imported"] == 0
        assert summary["files_skipped"] == 2

    def test_imported_rows_are_queryable(self, mirror, tmp_path):
        from sentinel_spr019.persistence.connection import connect

        db_path = tmp_path / "cli.db"
        main([str(mirror), "--db-path", str(db_path)])

        with connect(db_path) as conn:
            items = conn.execute("SELECT name FROM economy_items").fetchall()
            events = conn.execute("SELECT event_name FROM economy_events").fetchall()

        assert items == [("AKM",)]
        assert events == [("HeliCrash",)]


class TestDatabasePathResolution:
    def test_env_variable_is_used_when_no_flag_is_given(self, mirror, tmp_path, monkeypatch, capsys):
        db_path = tmp_path / "from-env.db"
        monkeypatch.setenv("SENTINEL_DB_PATH", str(db_path))

        assert main([str(mirror), "--json"]) == EXIT_OK
        assert json.loads(capsys.readouterr().out)["db_path"] == str(db_path)
        assert db_path.exists()

    def test_flag_beats_the_env_variable(self, mirror, tmp_path, monkeypatch, capsys):
        monkeypatch.setenv("SENTINEL_DB_PATH", str(tmp_path / "ignored.db"))
        chosen = tmp_path / "chosen.db"

        assert main([str(mirror), "--db-path", str(chosen), "--json"]) == EXIT_OK
        assert json.loads(capsys.readouterr().out)["db_path"] == str(chosen)
        assert chosen.exists()
        assert not (tmp_path / "ignored.db").exists()


class TestFailureHandling:
    def test_missing_mirror_root_exits_with_a_usage_error(self, tmp_path, capsys):
        exit_code = main([str(tmp_path / "nope"), "--db-path", str(tmp_path / "x.db")])

        assert exit_code == EXIT_USAGE
        assert "does not exist" in capsys.readouterr().err

    def test_a_failed_import_is_reported_via_the_exit_code(self, tmp_path, capsys):
        root = tmp_path / "broken"
        (root / "db").mkdir(parents=True)
        (root / "db" / "types.xml").write_text("<types><not-closed>", encoding="utf-8")

        exit_code = main([str(root), "--db-path", str(tmp_path / "broken.db"), "--json"])

        assert exit_code == EXIT_IMPORT_ERRORS
        summary = json.loads(capsys.readouterr().out)
        assert summary["status"] == "completed_with_errors"
        assert summary["files_failed"] == 1

    def test_no_arguments_exits_with_argparse_usage(self, capsys):
        with pytest.raises(SystemExit) as excinfo:
            main([])
        assert excinfo.value.code == EXIT_USAGE


class TestModuleInvocation:
    def test_python_m_entry_point_works(self, mirror, tmp_path):
        """Covers `python -m sentinel_spr019.importer`, the documented usage."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "sentinel_spr019.importer",
                str(mirror),
                "--db-path",
                str(tmp_path / "module.db"),
                "--json",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )

        assert result.returncode == EXIT_OK, result.stderr
        assert json.loads(result.stdout)["files_imported"] == 2

    def test_help_is_available(self):
        result = subprocess.run(
            [sys.executable, "-m", "sentinel_spr019.importer", "--help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )

        assert result.returncode == EXIT_OK
        assert "mirror_root" in result.stdout
        assert "--db-path" in result.stdout
