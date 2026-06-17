import logging
import sqlite3
import xml.etree.ElementTree as ET

LOGGER = logging.getLogger(__name__)

FLAG_FIELDS = (
    "count_in_cargo",
    "count_in_hoarder",
    "count_in_map",
    "count_in_player",
    "crafted",
    "deloot",
)

RELATION_TABLES = (
    ("category", "economy_categories", "economy_item_categories", "category_id"),
    ("usage", "economy_usages", "economy_item_usages", "usage_id"),
    ("value", "economy_values", "economy_item_values", "value_id"),
    ("tag", "economy_tags", "economy_item_tags", "tag_id"),
)

ALLOWED_TABLE_NAMES = {
    "economy_items",
    "economy_item_flags",
    "economy_categories",
    "economy_item_categories",
    "economy_usages",
    "economy_item_usages",
    "economy_values",
    "economy_item_values",
    "economy_tags",
    "economy_item_tags",
}

ALLOWED_FOREIGN_KEYS = {"category_id", "usage_id", "value_id", "tag_id"}


def import_types(xml_file, db_file):
    """
    Import economy items from types.xml into SQLite.

    The importer aligns the economy_items table with the fields currently used by
    the API (`name`, `nominal`, `min_value`, `max_value`, `restock`, `lifetime`)
    and populates related metadata tables when available.
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()

    conn = sqlite3.connect(db_file)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    inserted = 0
    updated = 0
    skipped = 0

    try:
        _ensure_schema(cur)

        for item in root.findall("type"):
            item_name = item.get("name")
            if not item_name:
                skipped += 1
                continue

            item_id, was_inserted = _upsert_item(cur, item_name, item)
            if was_inserted:
                inserted += 1
            else:
                updated += 1

            _sync_flags(cur, item_id, item.find("flags"))
            _sync_relations(cur, item_id, item)

        conn.commit()
    except Exception:
        conn.rollback()
        LOGGER.exception("Failed to import types from %s into %s", xml_file, db_file)
        raise
    finally:
        conn.close()

    print(
        f"import_types: inserted={inserted}, updated={updated}, skipped={skipped}"
    )
    return inserted, updated, skipped


def _ensure_schema(cur):
    _ensure_items_table(cur)
    _ensure_metadata_tables(cur)


def _ensure_items_table(cur):
    if not _table_exists(cur, "economy_items"):
        cur.execute(
            """
            CREATE TABLE economy_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                nominal INTEGER,
                lifetime INTEGER,
                restock INTEGER,
                min_value INTEGER,
                max_value INTEGER
            )
            """
        )
        return

    columns = _get_columns(cur, "economy_items")

    if "item_name" in columns and "name" not in columns:
        cur.execute("ALTER TABLE economy_items RENAME COLUMN item_name TO name")
        columns = _get_columns(cur, "economy_items")

    if "quantmin" in columns and "min_value" not in columns:
        cur.execute("ALTER TABLE economy_items RENAME COLUMN quantmin TO min_value")
        columns = _get_columns(cur, "economy_items")
    elif "min_value" not in columns:
        cur.execute("ALTER TABLE economy_items ADD COLUMN min_value INTEGER")
        columns = _get_columns(cur, "economy_items")

    if "quantmax" in columns and "max_value" not in columns:
        cur.execute("ALTER TABLE economy_items RENAME COLUMN quantmax TO max_value")
        columns = _get_columns(cur, "economy_items")
    elif "max_value" not in columns:
        cur.execute("ALTER TABLE economy_items ADD COLUMN max_value INTEGER")
        columns = _get_columns(cur, "economy_items")

    if "id" not in columns:
        cur.execute("ALTER TABLE economy_items ADD COLUMN id INTEGER")
        cur.execute("UPDATE economy_items SET id = rowid WHERE id IS NULL")

    cur.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_economy_items_id ON economy_items(id)"
    )
    cur.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_economy_items_name ON economy_items(name)"
    )


def _ensure_metadata_tables(cur):
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS economy_item_flags (
            item_id INTEGER PRIMARY KEY,
            count_in_cargo INTEGER,
            count_in_hoarder INTEGER,
            count_in_map INTEGER,
            count_in_player INTEGER,
            crafted INTEGER,
            deloot INTEGER,
            FOREIGN KEY(item_id) REFERENCES economy_items(id) ON DELETE CASCADE
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS economy_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS economy_item_categories (
            item_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            PRIMARY KEY(item_id, category_id),
            FOREIGN KEY(item_id) REFERENCES economy_items(id) ON DELETE CASCADE,
            FOREIGN KEY(category_id) REFERENCES economy_categories(id) ON DELETE CASCADE
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS economy_usages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS economy_item_usages (
            item_id INTEGER NOT NULL,
            usage_id INTEGER NOT NULL,
            PRIMARY KEY(item_id, usage_id),
            FOREIGN KEY(item_id) REFERENCES economy_items(id) ON DELETE CASCADE,
            FOREIGN KEY(usage_id) REFERENCES economy_usages(id) ON DELETE CASCADE
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS economy_values (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS economy_item_values (
            item_id INTEGER NOT NULL,
            value_id INTEGER NOT NULL,
            PRIMARY KEY(item_id, value_id),
            FOREIGN KEY(item_id) REFERENCES economy_items(id) ON DELETE CASCADE,
            FOREIGN KEY(value_id) REFERENCES economy_values(id) ON DELETE CASCADE
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS economy_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS economy_item_tags (
            item_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            PRIMARY KEY(item_id, tag_id),
            FOREIGN KEY(item_id) REFERENCES economy_items(id) ON DELETE CASCADE,
            FOREIGN KEY(tag_id) REFERENCES economy_tags(id) ON DELETE CASCADE
        )
        """
    )


def _upsert_item(cur, item_name, item):
    nominal = _parse_int(item.findtext("nominal"))
    lifetime = _parse_int(item.findtext("lifetime"))
    restock = _parse_int(item.findtext("restock"))
    min_value = _parse_int(item.findtext("quantmin"))
    max_value = _parse_int(item.findtext("quantmax"))

    cur.execute("SELECT id FROM economy_items WHERE name = ?", (item_name,))
    existing = cur.fetchone()

    if existing:
        item_id = existing[0]
        cur.execute(
            """
            UPDATE economy_items
            SET nominal = ?, lifetime = ?, restock = ?, min_value = ?, max_value = ?
            WHERE name = ?
            """,
            (nominal, lifetime, restock, min_value, max_value, item_name),
        )
        return item_id, False

    item_id = _next_item_id(cur)
    cur.execute(
        """
        INSERT INTO economy_items (id, name, nominal, lifetime, restock, min_value, max_value)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (item_id, item_name, nominal, lifetime, restock, min_value, max_value),
    )
    return item_id, True


def _sync_flags(cur, item_id, flags_element):
    cur.execute("DELETE FROM economy_item_flags WHERE item_id = ?", (item_id,))

    if flags_element is None:
        return

    values = [item_id]
    for field in FLAG_FIELDS:
        values.append(_parse_int(flags_element.get(field)))

    cur.execute(
        """
        INSERT INTO economy_item_flags (
            item_id,
            count_in_cargo,
            count_in_hoarder,
            count_in_map,
            count_in_player,
            crafted,
            deloot
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        tuple(values),
    )


def _sync_relations(cur, item_id, item):
    for element_name, lookup_table, join_table, foreign_key in RELATION_TABLES:
        related_names = [
            element.get("name")
            for element in item.findall(element_name)
            if element.get("name")
        ]
        _replace_relations(cur, item_id, related_names, lookup_table, join_table, foreign_key)


def _replace_relations(cur, item_id, names, lookup_table, join_table, foreign_key):
    lookup_table = _validate_identifier(lookup_table, ALLOWED_TABLE_NAMES)
    join_table = _validate_identifier(join_table, ALLOWED_TABLE_NAMES)
    foreign_key = _validate_identifier(foreign_key, ALLOWED_FOREIGN_KEYS)

    cur.execute(f"DELETE FROM {join_table} WHERE item_id = ?", (item_id,))

    for name in names:
        cur.execute(
            f"INSERT OR IGNORE INTO {lookup_table} (name) VALUES (?)",
            (name,),
        )
        cur.execute(
            f"SELECT id FROM {lookup_table} WHERE name = ?",
            (name,),
        )
        related_id = cur.fetchone()[0]
        cur.execute(
            f"INSERT OR IGNORE INTO {join_table} (item_id, {foreign_key}) VALUES (?, ?)",
            (item_id, related_id),
        )


def _next_item_id(cur):
    cur.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM economy_items")
    return cur.fetchone()[0]


def _table_exists(cur, table_name):
    cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    )
    return cur.fetchone() is not None


def _get_columns(cur, table_name):
    table_name = _validate_identifier(table_name, ALLOWED_TABLE_NAMES)
    cur.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cur.fetchall()]


def _parse_int(value):
    if value in (None, ""):
        return None
    return int(value)


def _validate_identifier(value, allowed_values):
    if value not in allowed_values:
        raise ValueError(f"Unsupported SQL identifier: {value}")
    return value
