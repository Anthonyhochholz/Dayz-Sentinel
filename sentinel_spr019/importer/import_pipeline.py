import hashlib
from pathlib import Path

from sentinel_spr019.api.repositories.import_tracking_repository import ImportTrackingRepository
from sentinel_spr019.importer.economy.events_importer import import_events
from sentinel_spr019.importer.economy.types_importer import import_types
from sentinel_spr019.importer.mirror_scanner import scan_mirror

try:
    from sentinel_spr019.importer.logs.adm_importer import import_adm, importer_version_for_hash
except ModuleNotFoundError:  # pragma: no cover - optional importer in partial environments
    import_adm = None
    importer_version_for_hash = None


SCANNER_VERSION = "mirror-scanner-v1"
IMPORTER_VERSION = "mirror-import-pipeline-v1"


def _default_db_path() -> str:
    return str(Path(__file__).resolve().parents[1] / "database" / "sqlite" / "sentinel.db")


def _compute_file_hash(file_path: str) -> str:
    """Return the SHA-256 digest for a file path using chunked reads."""
    digest = hashlib.sha256()
    with open(file_path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _importer_version_for_file(file_type: str, absolute_path: str) -> str:
    """Build a stable importer-version token for idempotent import tracking."""
    file_hash = _compute_file_hash(absolute_path)
    if file_type == "adm_log" and importer_version_for_hash is not None:
        return importer_version_for_hash(file_hash)
    return f"{IMPORTER_VERSION}:{file_type}:sha256={file_hash}"


def run_mirror_import(mirror_root: str, db_file: str | None = None) -> dict:
    database_path = db_file or _default_db_path()
    discovered_files = scan_mirror(mirror_root)

    scan_id = ImportTrackingRepository.start_scan(
        mirror_root=mirror_root,
        scanner_version=SCANNER_VERSION,
        db_path=database_path,
    )

    imported = 0
    skipped = 0
    unsupported = 0
    failed = 0

    try:
        for discovered in discovered_files:
            source_id = ImportTrackingRepository.get_or_create_source(
                source_name=discovered.relative_path,
                source_path=discovered.absolute_path,
                source_type=discovered.classification.file_type,
                db_path=database_path,
            )
            scan_file_id = ImportTrackingRepository.record_scan_file(
                scan_id=scan_id,
                source_id=source_id,
                relative_path=discovered.relative_path,
                absolute_path=discovered.absolute_path,
                file_size_bytes=discovered.size_bytes,
                file_type=discovered.classification.file_type,
                classifier_reason=discovered.classification.reason,
                is_supported=discovered.classification.should_import,
                import_status="classified",
                db_path=database_path,
            )

            if not discovered.classification.should_import:
                unsupported += 1
                ImportTrackingRepository.update_scan_file_status(
                    scan_file_id=scan_file_id,
                    import_status="unsupported",
                    db_path=database_path,
                )
                continue

            file_type = discovered.classification.file_type
            run_importer_version = _importer_version_for_file(file_type, discovered.absolute_path)

            if ImportTrackingRepository.has_completed_run_for_version(
                source_id, run_importer_version, database_path
            ):
                skipped += 1
                ImportTrackingRepository.update_scan_file_status(
                    scan_file_id=scan_file_id,
                    import_status="skipped",
                    db_path=database_path,
                )
                continue

            run_id = ImportTrackingRepository.create_import_run(
                source_id=source_id,
                importer_version=run_importer_version,
                db_path=database_path,
            )
            ImportTrackingRepository.attach_import_run(
                scan_file_id=scan_file_id,
                run_id=run_id,
                db_path=database_path,
            )

            try:
                if discovered.classification.file_type == "economy_types_xml":
                    import_types(discovered.absolute_path, database_path)
                elif discovered.classification.file_type == "economy_events_xml":
                    import_events(discovered.absolute_path, database_path)
                elif discovered.classification.file_type == "adm_log":
                    if import_adm is None:
                        raise RuntimeError("ADM importer is not available in this environment")
                    import_adm(discovered.absolute_path, database_path)
                else:
                    raise RuntimeError(f"No importer configured for file type: {file_type}")
            except Exception as exc:
                failed += 1
                ImportTrackingRepository.finish_import_run(run_id, "failed", db_path=database_path)
                ImportTrackingRepository.update_scan_file_status(
                    scan_file_id=scan_file_id,
                    import_status="failed",
                    error_message=str(exc),
                    db_path=database_path,
                )
                continue

            imported += 1
            ImportTrackingRepository.finish_import_run(run_id, "completed", db_path=database_path)
            ImportTrackingRepository.update_scan_file_status(
                scan_file_id=scan_file_id,
                import_status="imported",
                db_path=database_path,
            )
    finally:
        status = "completed" if failed == 0 else "completed_with_errors"
        ImportTrackingRepository.finish_scan(scan_id, status, db_path=database_path)

    return {
        "scan_id": scan_id,
        "status": status,
        "files_discovered": len(discovered_files),
        "files_imported": imported,
        "files_skipped": skipped,
        "files_unsupported": unsupported,
        "files_failed": failed,
    }
