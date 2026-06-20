import os
from pathlib import Path


def resolve_mirror_root(mirror_root: str | Path | None) -> str:
    configured_root = mirror_root if mirror_root is not None else os.getenv("MIRROR_ROOT")
    if configured_root is None or str(configured_root).strip() == "":
        raise ValueError("Mirror root is required. Set MIRROR_ROOT or pass mirror_root explicitly.")
    return str(Path(configured_root).expanduser().resolve())
