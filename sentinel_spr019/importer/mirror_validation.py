from collections import Counter
from pathlib import Path

from sentinel_spr019.importer.mirror_scanner import scan_mirror


def _format_path(path: str | Path) -> str:
    return str(Path(path).expanduser().resolve())


def validate_mirror(mirror_root: str | Path) -> dict:
    resolved_root = _format_path(mirror_root)
    discovered_files = scan_mirror(resolved_root)
    classification_counts = Counter(file.classification.file_type for file in discovered_files)
    supported_files = [file.relative_path for file in discovered_files if file.classification.should_import]
    unsupported_files = [file.relative_path for file in discovered_files if not file.classification.should_import]

    return {
        "mirror_root": resolved_root,
        "files_discovered": len(discovered_files),
        "classification_counts": dict(sorted(classification_counts.items())),
        "supported_files": supported_files,
        "unsupported_files": unsupported_files,
    }


def render_validation_summary(report: dict) -> str:
    lines = [
        "DayZ Mirror Validation Summary",
        f"Mirror root: {report['mirror_root']}",
        f"Files discovered: {report['files_discovered']}",
        "Classification counts:",
    ]

    for file_type, count in report["classification_counts"].items():
        lines.append(f"  - {file_type}: {count}")

    lines.append(f"Supported files ({len(report['supported_files'])}):")
    for relative_path in report["supported_files"]:
        lines.append(f"  - {relative_path}")

    lines.append(f"Unsupported files ({len(report['unsupported_files'])}):")
    for relative_path in report["unsupported_files"]:
        lines.append(f"  - {relative_path}")

    return "\n".join(lines)
