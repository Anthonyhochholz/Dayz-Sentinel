from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FileClassification:
    file_type: str
    should_import: bool
    reason: str


def classify_file(file_path: str | Path) -> FileClassification:
    path = Path(file_path)
    name = path.name.lower()
    suffix = path.suffix.lower()

    if name == "types.xml":
        return FileClassification(
            file_type="economy_types_xml",
            should_import=True,
            reason="filename matches types.xml",
        )

    if name == "events.xml":
        return FileClassification(
            file_type="economy_events_xml",
            should_import=True,
            reason="filename matches events.xml",
        )

    if suffix == ".xml":
        return FileClassification(
            file_type="xml_other",
            should_import=False,
            reason="xml file is unsupported by current parser set",
        )

    if suffix == ".adm":
        return FileClassification(
            file_type="adm_log",
            should_import=True,
            reason="adm log matched by extension",
        )

    if suffix == ".rpt":
        return FileClassification(
            file_type="rpt_log",
            should_import=False,
            reason="rpt log support is planned but not implemented",
        )

    return FileClassification(
        file_type="unknown",
        should_import=False,
        reason="file does not match any known import rule",
    )
