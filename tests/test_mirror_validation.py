import textwrap

from sentinel_spr019.importer.mirror_validation import render_validation_summary, validate_mirror


def test_validate_mirror_returns_discovery_statistics(tmp_path):
    mirror_root = tmp_path / "mirror"
    mirror_root.mkdir()
    (mirror_root / "types.xml").write_text(
        textwrap.dedent(
            """\
            <types>
              <type name="AKM">
                <nominal>3</nominal>
              </type>
            </types>
            """
        ),
        encoding="utf-8",
    )
    (mirror_root / "events.xml").write_text(
        textwrap.dedent(
            """\
            <events>
              <event name="ZmbM_Test">
                <nominal>1</nominal>
              </event>
            </events>
            """
        ),
        encoding="utf-8",
    )
    (mirror_root / "server.adm").write_text("dummy", encoding="utf-8")
    (mirror_root / "server.rpt").write_text("dummy", encoding="utf-8")
    (mirror_root / "notes.txt").write_text("dummy", encoding="utf-8")

    report = validate_mirror(mirror_root)

    assert report["mirror_root"] == str(mirror_root.resolve())
    assert report["files_discovered"] == 5
    assert report["classification_counts"] == {
        "adm_log": 1,
        "economy_events_xml": 1,
        "economy_types_xml": 1,
        "rpt_log": 1,
        "unknown": 1,
    }
    assert report["supported_files"] == ["events.xml", "server.adm", "types.xml"]
    assert report["unsupported_files"] == ["notes.txt", "server.rpt"]


def test_render_validation_summary_includes_all_sections(tmp_path):
    mirror_root = tmp_path / "mirror"
    mirror_root.mkdir()
    (mirror_root / "types.xml").write_text("<types />", encoding="utf-8")
    report = validate_mirror(mirror_root)

    summary = render_validation_summary(report)

    assert "DayZ Mirror Validation Summary" in summary
    assert f"Mirror root: {mirror_root.resolve()}" in summary
    assert "Files discovered: 1" in summary
    assert "Classification counts:" in summary
    assert "  - economy_types_xml: 1" in summary
    assert "Supported files (1):" in summary
    assert "  - types.xml" in summary
    assert "Unsupported files (0):" in summary
