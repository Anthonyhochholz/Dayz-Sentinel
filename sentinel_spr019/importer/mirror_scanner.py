from dataclasses import dataclass
from pathlib import Path

from sentinel_spr019.importer.file_classifier import FileClassification, classify_file


@dataclass(frozen=True)
class DiscoveredFile:
    absolute_path: str
    relative_path: str
    size_bytes: int
    classification: FileClassification


def scan_mirror(mirror_root: str | Path) -> list[DiscoveredFile]:
    root = Path(mirror_root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Mirror root does not exist or is not a directory: {root}")

    discovered: list[DiscoveredFile] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        classification = classify_file(path)
        discovered.append(
            DiscoveredFile(
                absolute_path=str(path),
                relative_path=str(path.relative_to(root)),
                size_bytes=path.stat().st_size,
                classification=classification,
            )
        )
    return discovered
