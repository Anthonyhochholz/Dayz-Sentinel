"""
pytest tests for sentinel_spr019.importer.economy.types_importer

Each test uses an isolated in-memory SQLite database so they are fully
independent and require no external files.
"""
import io
import sqlite3
import textwrap

import pytest

from sentinel_spr019.importer.economy.types_importer import import_types

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_xml(*items_xml: str) -> str:
    """Wrap item XML fragments inside a <types> root element."""
    inner = "\n".join(items_xml)
    return f"<types>\n{inner}\n</types>"


def _item(
    name="TestItem",
    nominal=10,
    lifetime=3600,
    restock=0,
    quantmin=1,
    quantmax=5,
    flags="",
    relations="",
):
    """Build a minimal <type> XML element string."""
    flags_tag = f"<flags {flags}/>" if flags else ""
    return textwrap.dedent(f"""\
        <type name="{name}">
            <nominal>{nominal}</nominal>
            <lifetime>{lifetime}</lifetime>
            <restock>{restock}</restock>
            <quantmin>{quantmin}</quantmin>
            <quantmax>{quantmax}</quantmax>
            {flags_tag}
            {relations}
        </type>""")


def _run(xml_content: str, db_path: str):
    """Write xml_content to a StringIO-like source and call import_types."""
    # import_types accepts a file path — use a tmp file helper via tmp_path fixture.
    # Callers that need a real file path use pytest's tmp_path; this wrapper is
    # only used when a real path is already available.
    return import_types(xml_content, db_path)


def _connect(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def db(tmp_path):
    """Return a path to a fresh temporary SQLite database file."""
    return str(tmp_path / "sentinel_test.db")


@pytest.fixture()
def xml_file(tmp_path):
    """Return a helper that writes XML to a temp file and returns its path."""
    def _write(content: str) -> str:
        p = tmp_path / "types.xml"
        p.write_text(content, encoding="utf-8")
        return str(p)
    return _write


# ---------------------------------------------------------------------------
# 1. Basic insert
# ---------------------------------------------------------------------------

class TestBasicInsert:
    def test_single_item_inserted(self, db, xml_file):
        xml = xml_file(_make_xml(_item("Rifle_1", nominal=5)))
        inserted, updated, skipped = import_types(xml, db)

        assert inserted == 1
        assert updated == 0
        assert skipped == 0

        with _connect(db) as conn:
            row = conn.execute("SELECT * FROM economy_items WHERE name = 'Rifle_1'").fetchone()
        assert row is not None
        assert row["nominal"] == 5

    def test_multiple_items_inserted(self, db, xml_file):
        xml = xml_file(_make_xml(_item("ItemA"), _item("ItemB"), _item("ItemC")))
        inserted, updated, skipped = import_types(xml, db)

        assert inserted == 3
        assert updated == 0

    def test_item_numeric_fields(self, db, xml_file):
        xml = xml_file(_make_xml(_item(
            "NumericItem",
            nominal=10,
            lifetime=7200,
            restock=120,
            quantmin=2,
            quantmax=8,
        )))
        import_types(xml, db)

        with _connect(db) as conn:
            row = conn.execute(
                "SELECT nominal, lifetime, restock, min_value, max_value "
                "FROM economy_items WHERE name = 'NumericItem'"
            ).fetchone()
        assert row["nominal"] == 10
        assert row["lifetime"] == 7200
        assert row["restock"] == 120
        assert row["min_value"] == 2
        assert row["max_value"] == 8

    def test_item_without_name_is_skipped(self, db, xml_file):
        xml = xml_file("<types><type><nominal>1</nominal></type></types>")
        inserted, updated, skipped = import_types(xml, db)

        assert inserted == 0
        assert skipped == 1


# ---------------------------------------------------------------------------
# 2. Upsert strategy — update existing entries
# ---------------------------------------------------------------------------

class TestUpsertStrategy:
    def test_reimport_updates_existing(self, db, xml_file):
        xml1 = xml_file(_make_xml(_item("Weapon", nominal=5, lifetime=1800)))
        import_types(xml1, db)

        xml2 = xml_file(_make_xml(_item("Weapon", nominal=15, lifetime=3600)))
        inserted, updated, skipped = import_types(xml2, db)

        assert inserted == 0
        assert updated == 1

        with _connect(db) as conn:
            row = conn.execute(
                "SELECT nominal, lifetime FROM economy_items WHERE name = 'Weapon'"
            ).fetchone()
        assert row["nominal"] == 15
        assert row["lifetime"] == 3600

    def test_idempotent_import(self, db, xml_file):
        xml = xml_file(_make_xml(_item("StableItem", nominal=3)))
        import_types(xml, db)
        import_types(xml, db)

        with _connect(db) as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM economy_items WHERE name = 'StableItem'"
            ).fetchone()[0]
        assert count == 1


# ---------------------------------------------------------------------------
# 3. Flags
# ---------------------------------------------------------------------------

class TestFlags:
    def test_flags_inserted(self, db, xml_file):
        xml = xml_file(_make_xml(_item(
            "FlagItem",
            flags="count_in_cargo='1' count_in_hoarder='0' count_in_map='1' "
                  "count_in_player='0' crafted='0' deloot='1'",
        )))
        import_types(xml, db)

        with _connect(db) as conn:
            item_id = conn.execute(
                "SELECT id FROM economy_items WHERE name = 'FlagItem'"
            ).fetchone()[0]
            flags = conn.execute(
                "SELECT * FROM economy_item_flags WHERE item_id = ?", (item_id,)
            ).fetchone()

        assert flags["count_in_cargo"] == 1
        assert flags["count_in_hoarder"] == 0
        assert flags["count_in_map"] == 1
        assert flags["deloot"] == 1

    def test_flags_updated_on_reimport(self, db, xml_file):
        xml1 = xml_file(_make_xml(_item("FlagUpdate", flags="deloot='0'")))
        import_types(xml1, db)

        xml2 = xml_file(_make_xml(_item("FlagUpdate", flags="deloot='1'")))
        import_types(xml2, db)

        with _connect(db) as conn:
            item_id = conn.execute(
                "SELECT id FROM economy_items WHERE name = 'FlagUpdate'"
            ).fetchone()[0]
            flags = conn.execute(
                "SELECT deloot FROM economy_item_flags WHERE item_id = ?", (item_id,)
            ).fetchone()
        assert flags["deloot"] == 1

    def test_item_without_flags_has_no_flags_row(self, db, xml_file):
        xml = xml_file(_make_xml(_item("NoFlagItem")))
        import_types(xml, db)

        with _connect(db) as conn:
            item_id = conn.execute(
                "SELECT id FROM economy_items WHERE name = 'NoFlagItem'"
            ).fetchone()[0]
            flags = conn.execute(
                "SELECT * FROM economy_item_flags WHERE item_id = ?", (item_id,)
            ).fetchone()
        assert flags is None


# ---------------------------------------------------------------------------
# 4. Categories
# ---------------------------------------------------------------------------

class TestCategories:
    def test_category_inserted(self, db, xml_file):
        xml = xml_file(_make_xml(
            _item("CatItem", relations='<category name="weapons"/>')
        ))
        import_types(xml, db)

        with _connect(db) as conn:
            cat = conn.execute(
                "SELECT id FROM economy_categories WHERE name = 'weapons'"
            ).fetchone()
        assert cat is not None

    def test_item_category_relation(self, db, xml_file):
        xml = xml_file(_make_xml(
            _item("CatItem", relations='<category name="weapons"/>')
        ))
        import_types(xml, db)

        with _connect(db) as conn:
            item_id = conn.execute(
                "SELECT id FROM economy_items WHERE name = 'CatItem'"
            ).fetchone()[0]
            rel = conn.execute(
                "SELECT * FROM economy_item_categories WHERE item_id = ?", (item_id,)
            ).fetchone()
        assert rel is not None

    def test_shared_category_deduplicated(self, db, xml_file):
        xml = xml_file(_make_xml(
            _item("ItemX", relations='<category name="tools"/>'),
            _item("ItemY", relations='<category name="tools"/>'),
        ))
        import_types(xml, db)

        with _connect(db) as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM economy_categories WHERE name = 'tools'"
            ).fetchone()[0]
        assert count == 1


# ---------------------------------------------------------------------------
# 5. Usages
# ---------------------------------------------------------------------------

class TestUsages:
    def test_usage_inserted_and_linked(self, db, xml_file):
        xml = xml_file(_make_xml(
            _item("UsageItem", relations='<usage name="Military"/>')
        ))
        import_types(xml, db)

        with _connect(db) as conn:
            usage = conn.execute(
                "SELECT id FROM economy_usages WHERE name = 'Military'"
            ).fetchone()
            assert usage is not None

            item_id = conn.execute(
                "SELECT id FROM economy_items WHERE name = 'UsageItem'"
            ).fetchone()[0]
            rel = conn.execute(
                "SELECT * FROM economy_item_usages WHERE item_id = ?", (item_id,)
            ).fetchone()
        assert rel is not None


# ---------------------------------------------------------------------------
# 6. Values
# ---------------------------------------------------------------------------

class TestValues:
    def test_value_inserted_and_linked(self, db, xml_file):
        xml = xml_file(_make_xml(
            _item("ValueItem", relations='<value name="Tier1"/>')
        ))
        import_types(xml, db)

        with _connect(db) as conn:
            val = conn.execute(
                "SELECT id FROM economy_values WHERE name = 'Tier1'"
            ).fetchone()
            assert val is not None

            item_id = conn.execute(
                "SELECT id FROM economy_items WHERE name = 'ValueItem'"
            ).fetchone()[0]
            rel = conn.execute(
                "SELECT * FROM economy_item_values WHERE item_id = ?", (item_id,)
            ).fetchone()
        assert rel is not None


# ---------------------------------------------------------------------------
# 7. Tags
# ---------------------------------------------------------------------------

class TestTags:
    def test_tag_inserted_and_linked(self, db, xml_file):
        xml = xml_file(_make_xml(
            _item("TagItem", relations='<tag name="inventory"/>')
        ))
        import_types(xml, db)

        with _connect(db) as conn:
            tag = conn.execute(
                "SELECT id FROM economy_tags WHERE name = 'inventory'"
            ).fetchone()
            assert tag is not None

            item_id = conn.execute(
                "SELECT id FROM economy_items WHERE name = 'TagItem'"
            ).fetchone()[0]
            rel = conn.execute(
                "SELECT * FROM economy_item_tags WHERE item_id = ?", (item_id,)
            ).fetchone()
        assert rel is not None


# ---------------------------------------------------------------------------
# 8. Multiple relations per item
# ---------------------------------------------------------------------------

class TestMultipleRelations:
    def test_multiple_usages(self, db, xml_file):
        xml = xml_file(_make_xml(
            _item(
                "MultiUsage",
                relations='<usage name="Military"/><usage name="Town"/>',
            )
        ))
        import_types(xml, db)

        with _connect(db) as conn:
            item_id = conn.execute(
                "SELECT id FROM economy_items WHERE name = 'MultiUsage'"
            ).fetchone()[0]
            count = conn.execute(
                "SELECT COUNT(*) FROM economy_item_usages WHERE item_id = ?", (item_id,)
            ).fetchone()[0]
        assert count == 2

    def test_relations_replaced_on_reimport(self, db, xml_file):
        xml1 = xml_file(_make_xml(
            _item("Changeable", relations='<category name="food"/><category name="drink"/>')
        ))
        import_types(xml1, db)

        xml2 = xml_file(_make_xml(
            _item("Changeable", relations='<category name="weapons"/>')
        ))
        import_types(xml2, db)

        with _connect(db) as conn:
            item_id = conn.execute(
                "SELECT id FROM economy_items WHERE name = 'Changeable'"
            ).fetchone()[0]
            count = conn.execute(
                "SELECT COUNT(*) FROM economy_item_categories WHERE item_id = ?", (item_id,)
            ).fetchone()[0]
        assert count == 1


# ---------------------------------------------------------------------------
# 9. Transaction integrity — partial failure rolls back
# ---------------------------------------------------------------------------

class TestTransactions:
    def test_rollback_on_error(self, db, xml_file, monkeypatch):
        """If the importer raises mid-import, no rows must be persisted."""
        call_count = {"n": 0}
        original_upsert = __import__(
            "sentinel_spr019.importer.economy.types_importer",
            fromlist=["_upsert_item"],
        )._upsert_item

        def _failing_upsert(cur, item_name, item):
            call_count["n"] += 1
            if call_count["n"] == 2:
                raise RuntimeError("Simulated mid-import failure")
            return original_upsert(cur, item_name, item)

        monkeypatch.setattr(
            "sentinel_spr019.importer.economy.types_importer._upsert_item",
            _failing_upsert,
        )

        xml = xml_file(_make_xml(_item("ItemFirst"), _item("ItemFails"), _item("ItemThird")))
        with pytest.raises(RuntimeError, match="Simulated mid-import failure"):
            import_types(xml, db)

        with _connect(db) as conn:
            count = conn.execute("SELECT COUNT(*) FROM economy_items").fetchone()[0]
        assert count == 0


# ---------------------------------------------------------------------------
# 10. Schema migration — legacy column names are renamed transparently
# ---------------------------------------------------------------------------

class TestSchemaMigration:
    def test_legacy_item_name_column_migrated(self, db, xml_file):
        """If economy_items exists with item_name instead of name, it is renamed."""
        with sqlite3.connect(db) as conn:
            conn.execute(
                """
                CREATE TABLE economy_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_name TEXT NOT NULL UNIQUE,
                    nominal INTEGER,
                    lifetime INTEGER,
                    restock INTEGER,
                    quantmin INTEGER,
                    quantmax INTEGER
                )
                """
            )

        xml = xml_file(_make_xml(_item("MigratedItem", nominal=7)))
        inserted, updated, skipped = import_types(xml, db)

        assert inserted == 1
        with _connect(db) as conn:
            row = conn.execute(
                "SELECT nominal FROM economy_items WHERE name = 'MigratedItem'"
            ).fetchone()
        assert row["nominal"] == 7

    def test_legacy_quantmin_quantmax_columns_migrated(self, db, xml_file):
        """quantmin/quantmax columns are renamed to min_value/max_value."""
        with sqlite3.connect(db) as conn:
            conn.execute(
                """
                CREATE TABLE economy_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    nominal INTEGER,
                    lifetime INTEGER,
                    restock INTEGER,
                    quantmin INTEGER,
                    quantmax INTEGER
                )
                """
            )

        xml = xml_file(_make_xml(_item("Quant", quantmin=2, quantmax=6)))
        import_types(xml, db)

        with _connect(db) as conn:
            row = conn.execute(
                "SELECT min_value, max_value FROM economy_items WHERE name = 'Quant'"
            ).fetchone()
        assert row["min_value"] == 2
        assert row["max_value"] == 6


# ---------------------------------------------------------------------------
# 11. Large import
# ---------------------------------------------------------------------------

class TestLargeImport:
    def test_hundred_items(self, db, xml_file):
        items = [_item(f"Item_{i:03d}", nominal=i % 20) for i in range(100)]
        xml = xml_file(_make_xml(*items))
        inserted, updated, skipped = import_types(xml, db)

        assert inserted == 100
        assert updated == 0
        assert skipped == 0

        with _connect(db) as conn:
            count = conn.execute("SELECT COUNT(*) FROM economy_items").fetchone()[0]
        assert count == 100
