import hashlib
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path


_HEADER_RE = re.compile(r"^AdminLog started on (\d{4}-\d{2}-\d{2}) at (\d{2}:\d{2}:\d{2})$")
_TIME_PREFIX_RE = re.compile(r"^(\d{2}:\d{2}:\d{2}) \| (.+)$")

_CONNECTED_RE = re.compile(
    r'^Player "(?P<name>.+?)" \(id=(?P<uid>\d+)\s+pos=<(?P<x>-?\d+(?:\.\d+)?),\s*(?P<y>-?\d+(?:\.\d+)?),\s*(?P<z>-?\d+(?:\.\d+)?)>\) is connected$'
)
_DISCONNECTED_RE = re.compile(
    r'^Player "(?P<name>.+?)" \(id=(?P<uid>\d+)(?:\s+pos=<(?P<x>-?\d+(?:\.\d+)?),\s*(?P<y>-?\d+(?:\.\d+)?),\s*(?P<z>-?\d+(?:\.\d+)?)>)?\) has been disconnected(?: after \d+s)?$'
)
_KILLED_RE = re.compile(
    r'^Player "(?P<victim_name>.+?)" \(id=(?P<victim_uid>\d+)\s+pos=<(?P<victim_x>-?\d+(?:\.\d+)?),\s*(?P<victim_y>-?\d+(?:\.\d+)?),\s*(?P<victim_z>-?\d+(?:\.\d+)?)>\) '
    r'killed by Player "(?P<killer_name>.+?)" \(id=(?P<killer_uid>\d+)\s+pos=<(?P<killer_x>-?\d+(?:\.\d+)?),\s*(?P<killer_y>-?\d+(?:\.\d+)?),\s*(?P<killer_z>-?\d+(?:\.\d+)?)>\) '
    r'with (?P<weapon>.+?) from (?P<distance>-?\d+(?:\.\d+)?) meters$'
)
_DIED_RE = re.compile(r'^Player "(?P<name>.+?)" \(id=(?P<uid>\d+)(?:\s+pos=<(?P<x>-?\d+(?:\.\d+)?),\s*(?P<y>-?\d+(?:\.\d+)?),\s*(?P<z>-?\d+(?:\.\d+)?)>)?\) died\..*$')
_ADMIN_ACTION_RE = re.compile(
    r'^Admin "(?P<name>.+?)" \(id=(?P<uid>\d+)\): (?P<action>.+)$'
)


@dataclass(frozen=True)
class ConnectedEvent:
    timestamp: str
    player_uid: str
    player_name: str
    pos_x: float | None
    pos_y: float | None
    pos_z: float | None


@dataclass(frozen=True)
class DisconnectedEvent:
    timestamp: str
    player_uid: str
    player_name: str
    pos_x: float | None
    pos_y: float | None
    pos_z: float | None


@dataclass(frozen=True)
class KilledEvent:
    timestamp: str
    victim_uid: str
    victim_name: str
    killer_uid: str
    killer_name: str
    weapon: str
    distance: float | None
    victim_pos_x: float | None
    victim_pos_y: float | None
    victim_pos_z: float | None
    killer_pos_x: float | None
    killer_pos_y: float | None
    killer_pos_z: float | None


@dataclass(frozen=True)
class DiedEvent:
    timestamp: str
    player_uid: str
    player_name: str
    pos_x: float | None
    pos_y: float | None
    pos_z: float | None


@dataclass(frozen=True)
class AdminActionEvent:
    timestamp: str
    admin_uid: str
    admin_name: str
    action_text: str


def compute_file_hash(file_path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(file_path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def importer_version_for_hash(file_hash: str) -> str:
    return f"adm-importer-v1:sha256={file_hash}"


def parse_adm(file_path: str | Path) -> tuple[str, list]:
    start_time = ""
    start_date = ""
    events: list = []

    path = Path(file_path)
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue

        header_match = _HEADER_RE.match(line)
        if header_match:
            start_date = header_match.group(1)
            start_time = f"{header_match.group(1)} {header_match.group(2)}"
            continue

        timed_match = _TIME_PREFIX_RE.match(line)
        if not timed_match:
            continue

        event_time = timed_match.group(1)
        payload = timed_match.group(2).strip()
        timestamp = f"{start_date} {event_time}" if start_date else event_time

        connected_match = _CONNECTED_RE.match(payload)
        if connected_match:
            events.append(
                ConnectedEvent(
                    timestamp=timestamp,
                    player_uid=connected_match.group("uid"),
                    player_name=connected_match.group("name"),
                    pos_x=float(connected_match.group("x")),
                    pos_y=float(connected_match.group("y")),
                    pos_z=float(connected_match.group("z")),
                )
            )
            continue

        disconnected_match = _DISCONNECTED_RE.match(payload)
        if disconnected_match:
            events.append(
                DisconnectedEvent(
                    timestamp=timestamp,
                    player_uid=disconnected_match.group("uid"),
                    player_name=disconnected_match.group("name"),
                    pos_x=_float_or_none(disconnected_match.group("x")),
                    pos_y=_float_or_none(disconnected_match.group("y")),
                    pos_z=_float_or_none(disconnected_match.group("z")),
                )
            )
            continue

        killed_match = _KILLED_RE.match(payload)
        if killed_match:
            events.append(
                KilledEvent(
                    timestamp=timestamp,
                    victim_uid=killed_match.group("victim_uid"),
                    victim_name=killed_match.group("victim_name"),
                    killer_uid=killed_match.group("killer_uid"),
                    killer_name=killed_match.group("killer_name"),
                    weapon=killed_match.group("weapon"),
                    distance=_float_or_none(killed_match.group("distance")),
                    victim_pos_x=_float_or_none(killed_match.group("victim_x")),
                    victim_pos_y=_float_or_none(killed_match.group("victim_y")),
                    victim_pos_z=_float_or_none(killed_match.group("victim_z")),
                    killer_pos_x=_float_or_none(killed_match.group("killer_x")),
                    killer_pos_y=_float_or_none(killed_match.group("killer_y")),
                    killer_pos_z=_float_or_none(killed_match.group("killer_z")),
                )
            )
            continue

        died_match = _DIED_RE.match(payload)
        if died_match:
            events.append(
                DiedEvent(
                    timestamp=timestamp,
                    player_uid=died_match.group("uid"),
                    player_name=died_match.group("name"),
                    pos_x=_float_or_none(died_match.group("x")),
                    pos_y=_float_or_none(died_match.group("y")),
                    pos_z=_float_or_none(died_match.group("z")),
                )
            )
            continue

        admin_match = _ADMIN_ACTION_RE.match(payload)
        if admin_match:
            events.append(
                AdminActionEvent(
                    timestamp=timestamp,
                    admin_uid=admin_match.group("uid"),
                    admin_name=admin_match.group("name"),
                    action_text=admin_match.group("action"),
                )
            )

    return start_time, events


def import_adm(file_path: str | Path, db_file: str) -> tuple[int, int]:
    start_time, events = parse_adm(file_path)
    stored = 0
    skipped = 0

    conn = sqlite3.connect(db_file)
    cur = conn.cursor()

    try:
        server_session_id = _get_or_create_server_session(cur, start_time)
        if server_session_id["stored"]:
            stored += 1
        else:
            skipped += 1

        for event in events:
            if isinstance(event, ConnectedEvent):
                result = _store_connected(cur, event)
            elif isinstance(event, DisconnectedEvent):
                result = _store_disconnected(cur, event)
            elif isinstance(event, KilledEvent):
                result = _store_killed(cur, event)
            elif isinstance(event, DiedEvent):
                result = _store_died(cur, event)
            elif isinstance(event, AdminActionEvent):
                result = _store_admin_action(cur, event)
            else:
                skipped += 1
                continue

            stored += result["stored"]
            skipped += result["skipped"]

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return stored, skipped


def _float_or_none(value: str | None) -> float | None:
    if value is None:
        return None
    return float(value)


def _get_or_create_player(cur, player_uid: str, player_name: str) -> tuple[int, bool]:
    cur.execute("SELECT id, player_name FROM players WHERE player_uid = ?", (player_uid,))
    row = cur.fetchone()
    if row:
        player_id, existing_name = row
        if player_name and existing_name != player_name:
            cur.execute(
                "UPDATE players SET player_name = ? WHERE id = ?",
                (player_name, player_id),
            )
        return player_id, False

    cur.execute(
        "INSERT INTO players (player_uid, player_name) VALUES (?, ?)",
        (player_uid, player_name),
    )
    return cur.lastrowid, True


def _get_or_create_server_session(cur, start_time: str) -> dict[str, int]:
    cur.execute(
        """
        SELECT id
        FROM server_sessions
        WHERE executable = 'adm_log'
          AND (
              (start_time IS NULL AND ? IS NULL)
              OR start_time = ?
          )
        """,
        (start_time or None, start_time or None),
    )
    row = cur.fetchone()
    if row:
        return {"id": row[0], "stored": 0}

    cur.execute(
        "INSERT INTO server_sessions (start_time, executable) VALUES (?, ?)",
        (start_time or None, "adm_log"),
    )
    return {"id": cur.lastrowid, "stored": 1}


def _store_connected(cur, event: ConnectedEvent) -> dict[str, int]:
    player_id, player_inserted = _get_or_create_player(cur, event.player_uid, event.player_name)
    stored = 1 if player_inserted else 0
    skipped = 0 if player_inserted else 1

    cur.execute(
        "SELECT id FROM player_sessions WHERE player_id = ? AND connect_time = ?",
        (player_id, event.timestamp),
    )
    if cur.fetchone():
        return {"stored": stored, "skipped": skipped + 1}

    cur.execute(
        "INSERT INTO player_sessions (player_id, connect_time) VALUES (?, ?)",
        (player_id, event.timestamp),
    )
    return {"stored": stored + 1, "skipped": skipped}


def _store_disconnected(cur, event: DisconnectedEvent) -> dict[str, int]:
    player_id, player_inserted = _get_or_create_player(cur, event.player_uid, event.player_name)
    stored = 1 if player_inserted else 0
    skipped = 0 if player_inserted else 1

    cur.execute(
        """
        SELECT id, disconnect_time
        FROM player_sessions
        WHERE player_id = ? AND disconnect_time IS NULL
        ORDER BY id DESC
        LIMIT 1
        """,
        (player_id,),
    )
    open_session = cur.fetchone()
    if open_session:
        session_id, disconnect_time = open_session
        if disconnect_time == event.timestamp:
            return {"stored": stored, "skipped": skipped + 1}
        cur.execute(
            "UPDATE player_sessions SET disconnect_time = ? WHERE id = ?",
            (event.timestamp, session_id),
        )
        return {"stored": stored + 1, "skipped": skipped}

    cur.execute(
        "SELECT id FROM player_sessions WHERE player_id = ? AND disconnect_time = ?",
        (player_id, event.timestamp),
    )
    if cur.fetchone():
        return {"stored": stored, "skipped": skipped + 1}

    # Preserve orphan disconnect events deterministically when no matching connect event exists.
    cur.execute(
        "INSERT INTO player_sessions (player_id, connect_time, disconnect_time) VALUES (?, ?, ?)",
        (player_id, event.timestamp, event.timestamp),
    )
    return {"stored": stored + 1, "skipped": skipped}


def _store_killed(cur, event: KilledEvent) -> dict[str, int]:
    victim_id, victim_inserted = _get_or_create_player(cur, event.victim_uid, event.victim_name)
    killer_id, killer_inserted = _get_or_create_player(cur, event.killer_uid, event.killer_name)
    cur.execute("SELECT player_uid FROM players WHERE id = ?", (killer_id,))
    killer_uid_row = cur.fetchone()
    killer_uid = killer_uid_row[0] if killer_uid_row else event.killer_uid

    stored = (1 if victim_inserted else 0) + (1 if killer_inserted else 0)
    skipped = (0 if victim_inserted else 1) + (0 if killer_inserted else 1)

    cur.execute(
        """
        SELECT id FROM player_damage_events
        WHERE player_id = ? AND timestamp = ? AND source = ? AND weapon = ?
        """,
        (victim_id, event.timestamp, killer_uid, event.weapon),
    )
    if cur.fetchone():
        return {"stored": stored, "skipped": skipped + 1}

    cur.execute(
        """
        INSERT INTO player_damage_events (
            player_id, timestamp, source, weapon, damage, pos_x, pos_y, pos_z
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            victim_id,
            event.timestamp,
            killer_uid,
            event.weapon,
            None,
            event.victim_pos_x,
            event.victim_pos_y,
            event.victim_pos_z,
        ),
    )
    return {"stored": stored + 1, "skipped": skipped}


def _store_died(cur, event: DiedEvent) -> dict[str, int]:
    player_id, player_inserted = _get_or_create_player(cur, event.player_uid, event.player_name)
    stored = 1 if player_inserted else 0
    skipped = 0 if player_inserted else 1

    cur.execute(
        """
        SELECT id FROM player_actions
        WHERE player_id = ? AND timestamp = ? AND action_name = 'died'
        """,
        (player_id, event.timestamp),
    )
    if cur.fetchone():
        return {"stored": stored, "skipped": skipped + 1}

    cur.execute(
        "INSERT INTO player_actions (player_id, timestamp, action_name, item_name) VALUES (?, ?, ?, ?)",
        (player_id, event.timestamp, "died", None),
    )
    return {"stored": stored + 1, "skipped": skipped}


def _store_admin_action(cur, event: AdminActionEvent) -> dict[str, int]:
    admin_id, admin_inserted = _get_or_create_player(cur, event.admin_uid, event.admin_name)
    stored = 1 if admin_inserted else 0
    skipped = 0 if admin_inserted else 1

    cur.execute(
        """
        SELECT id FROM player_actions
        WHERE player_id = ? AND timestamp = ? AND action_name = 'admin_action' AND item_name = ?
        """,
        (admin_id, event.timestamp, event.action_text),
    )
    if cur.fetchone():
        return {"stored": stored, "skipped": skipped + 1}

    cur.execute(
        "INSERT INTO player_actions (player_id, timestamp, action_name, item_name) VALUES (?, ?, ?, ?)",
        (admin_id, event.timestamp, "admin_action", event.action_text),
    )
    return {"stored": stored + 1, "skipped": skipped}
