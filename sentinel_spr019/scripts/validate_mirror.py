import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sentinel_spr019.importer.mirror_validation import render_validation_summary, validate_mirror


def _resolve_mirror_root(mirror_root: str | None) -> str:
    configured_root = mirror_root if mirror_root is not None else os.getenv("MIRROR_ROOT")
    if configured_root is None or configured_root.strip() == "":
        raise ValueError("Mirror root is required. Set MIRROR_ROOT or pass --mirror-root.")
    return str(Path(configured_root).expanduser().resolve())


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a DayZ mirror directory.")
    parser.add_argument("--mirror-root", help="Path to the DayZ mirror root directory.")
    args = parser.parse_args()

    try:
        mirror_root = _resolve_mirror_root(args.mirror_root)
        report = validate_mirror(mirror_root)
    except Exception as exc:
        print(f"Validation failed: {exc}")
        return 1

    print(render_validation_summary(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
