from pydantic import BaseModel, ConfigDict, Field


class MirrorScan(BaseModel):
    """A single mirror scan recorded by the import pipeline."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    mirror_root: str
    started_at: str
    finished_at: str | None = None
    status: str
    scanner_version: str | None = None


class MirrorScanFile(BaseModel):
    """A file discovered during a mirror scan, with its classification result."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    scan_id: int
    source_id: int | None = None
    relative_path: str
    absolute_path: str
    file_size_bytes: int | None = None
    file_type: str
    classifier_reason: str | None = None
    is_supported: bool
    import_run_id: int | None = None
    import_status: str
    error_message: str | None = None
    created_at: str


class ImportRun(BaseModel):
    """An import run, joined with the source it processed."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    started_at: str
    finished_at: str | None = None
    status: str
    importer_version: str | None = None
    source_id: int | None = None
    source_name: str | None = None
    source_path: str | None = None
    source_type: str | None = None


class MirrorScanListResponse(BaseModel):
    """Paginated mirror-scan collection.

    Unlike the economy collections this envelope carries no `total`, because
    the repository does not run a count query for scans.
    """

    data: list[MirrorScan]
    limit: int
    offset: int


class MirrorScanFileListResponse(BaseModel):
    """Paginated collection of files belonging to one scan."""

    data: list[MirrorScanFile]
    scan_id: int = Field(description="The scan the returned files belong to")
    limit: int
    offset: int


class ImportRunListResponse(BaseModel):
    """Paginated import-run collection."""

    data: list[ImportRun]
    limit: int
    offset: int
