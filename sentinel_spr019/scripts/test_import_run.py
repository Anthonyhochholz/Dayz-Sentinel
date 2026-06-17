# SPR-010
# Test import bootstrap runner

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sentinel_spr019.importer.economy.types_importer import import_types


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python sentinel_spr019/scripts/test_import_run.py <types.xml> <sentinel.db>")
        raise SystemExit(1)

    inserted, updated, skipped = import_types(sys.argv[1], sys.argv[2])
    print(
        f"types.xml import complete: inserted={inserted}, updated={updated}, skipped={skipped}"
    )
