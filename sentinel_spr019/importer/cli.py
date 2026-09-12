"""Command-line entry point for the mirror import pipeline.

Usage:
    python -m sentinel_spr019.importer /path/to/mirror
    python -m sentinel_spr019.importer /path/to/mirror --db-path ./sentinel.db --json
"""

import argparse
import json
import logging
import os
import sys

from sentinel_spr019.importer.import_pipeline import run_mirror_import
from sentinel_spr019.persistence.connection import default_db_path

LOGGER = logging.getLogger("sentinel.importer")

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_IMPORT_ERRORS = 1

_SUMMARY_LABELS = (
    ("files_discovered", "discovered"),
    ("files_imported", "imported"),
    ("files_skipped", "skipped (unchanged)"),
    ("files_unsupported", "unsupported"),
    ("files_failed", "failed"),
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m sentinel_spr019.importer",
        description="Scan a DayZ server mirror directory and import the supported files.",
    )
    parser.add_argument(
        "mirror_root",
        help="Directory to scan recursively for types.xml, events.xml and *.adm files.",
    )
    parser.add_argument(
        "--db-path",
        default=None,
        help=(
            "SQLite database to import into. "
            "Defaults to $SENTINEL_DB_PATH, then the packaged database path."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Print the run summary as JSON instead of human-readable text.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser


def _resolve_db_path(explicit: str | None) -> str:
    if explicit:
        return explicit
    return os.getenv("SENTINEL_DB_PATH") or default_db_path()


def _format_summary(summary: dict, db_path: str) -> str:
    lines = [
        f"Mirror import {summary['status']} (scan #{summary['scan_id']})",
        f"  database: {db_path}",
    ]
    width = max(len(label) for _, label in _SUMMARY_LABELS)
    for key, label in _SUMMARY_LABELS:
        lines.append(f"  {label + ':':<{width + 1}} {summary[key]}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    db_path = _resolve_db_path(args.db_path)

    try:
        summary = run_mirror_import(args.mirror_root, db_path)
    except ValueError as exc:
        # scan_mirror rejects a missing or non-directory mirror root.
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE

    if args.as_json:
        print(json.dumps({**summary, "db_path": db_path}, indent=2))
    else:
        print(_format_summary(summary, db_path))

    if summary["files_failed"]:
        LOGGER.error(
            "%s file(s) failed to import; see the import_runs table for details",
            summary["files_failed"],
        )
        return EXIT_IMPORT_ERRORS

    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
