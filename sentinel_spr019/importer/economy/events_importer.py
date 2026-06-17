import sqlite3
import xml.etree.ElementTree as ET


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
    skipped = 0

    for event in root.findall('event'):
        name        = event.get('name')
        nominal     = event.findtext('nominal')
        min_count   = event.findtext('min')
        max_count   = event.findtext('max')
        lifetime    = event.findtext('lifetime')
        restock     = event.findtext('restock')
        saferadius  = event.findtext('saferadius')
        distradius  = event.findtext('distanceradius')
        cleanradius = event.findtext('cleanupradius')
        position    = event.findtext('position')
        limit       = event.findtext('limit')
        active      = event.findtext('active')

        try:
            cur.execute(
                """INSERT INTO economy_events
                   (event_name, nominal, min_count, max_count,
                    lifetime, restock, saferadius, distanceradius, cleanupradius,
                    position_mode, limit_mode, active)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (name,
                 int(nominal)      if nominal     else None,
                 int(min_count)    if min_count   else None,
                 int(max_count)    if max_count   else None,
                 int(lifetime)     if lifetime    else None,
                 int(restock)      if restock     else None,
                 float(saferadius) if saferadius  else None,
                 float(distradius) if distradius  else None,
                 float(cleanradius)if cleanradius else None,
                 position, limit,
                 int(active) if active else None)
            )
            inserted += 1
        except sqlite3.IntegrityError:
            skipped += 1

    conn.commit()
    conn.close()
    print(f"import_events: inserted={inserted}, skipped={skipped}")
    return inserted, skipped
