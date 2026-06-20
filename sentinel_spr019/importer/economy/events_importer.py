import logging
import sqlite3
import xml.etree.ElementTree as ET

LOGGER = logging.getLogger(__name__)


def import_events(xml_file, db_file):
    """
    SPR-019: Import economy events from events.xml into economy_events table.
    Captures all fields: nominal, min/max, lifetime, restock, radii, position, limit, active.
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()

    conn = sqlite3.connect(db_file)
    cur = conn.cursor()

    inserted = 0
    updated = 0
    skipped = 0

    try:
        for event in root.findall("event"):
            name = event.get("name")
            if not name:
                skipped += 1
                LOGGER.warning("Skipping event without name in %s", xml_file)
                continue

            payload = (
                _parse_int(event.findtext("nominal"), "nominal"),
                _parse_int(event.findtext("min"), "min"),
                _parse_int(event.findtext("max"), "max"),
                _parse_int(event.findtext("lifetime"), "lifetime"),
                _parse_int(event.findtext("restock"), "restock"),
                _parse_float(event.findtext("saferadius"), "saferadius"),
                _parse_float(event.findtext("distanceradius"), "distanceradius"),
                _parse_float(event.findtext("cleanupradius"), "cleanupradius"),
                event.findtext("position"),
                event.findtext("limit"),
                _parse_int(event.findtext("active"), "active"),
                name,
            )

            cur.execute("SELECT id FROM economy_events WHERE event_name = ?", (name,))
            existing = cur.fetchone()
            if existing:
                cur.execute(
                    """
                    UPDATE economy_events
                    SET nominal = ?, min_count = ?, max_count = ?, lifetime = ?, restock = ?,
                        saferadius = ?, distanceradius = ?, cleanupradius = ?, position_mode = ?,
                        limit_mode = ?, active = ?
                    WHERE event_name = ?
                    """,
                    payload,
                )
                updated += 1
            else:
                cur.execute(
                    """
                    INSERT INTO economy_events
                        (nominal, min_count, max_count, lifetime, restock,
                         saferadius, distanceradius, cleanupradius, position_mode,
                         limit_mode, active, event_name)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    payload,
                )
                inserted += 1

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    print(f"import_events: inserted={inserted}, updated={updated}, skipped={skipped}")
    return inserted, updated, skipped


def _parse_int(value, field_name: str) -> int | None:
    """Parse integer values while preserving NULL semantics for empty fields."""
    if value in (None, ""):
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"Invalid integer for field '{field_name}': {value}") from exc


def _parse_float(value, field_name: str) -> float | None:
    """Parse float values while preserving NULL semantics for empty fields."""
    if value in (None, ""):
        return None
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"Invalid float for field '{field_name}': {value}") from exc
