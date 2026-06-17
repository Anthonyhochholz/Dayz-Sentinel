
-- DEV-003 Schema Revision 2 (delta from DEV-001)

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS import_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL UNIQUE,
    source_path TEXT,
    source_type TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS import_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    importer_version TEXT,
    source_id INTEGER,
    FOREIGN KEY(source_id) REFERENCES import_sources(id)
);

CREATE TABLE IF NOT EXISTS localization_errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    timestamp TEXT,
    missing_key TEXT NOT NULL,
    FOREIGN KEY(session_id) REFERENCES server_sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS network_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    timestamp TEXT,
    event_type TEXT NOT NULL,
    details TEXT,
    FOREIGN KEY(session_id) REFERENCES server_sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS script_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_file TEXT NOT NULL,
    start_time TEXT
);

CREATE TABLE IF NOT EXISTS script_engine_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    event_text TEXT NOT NULL,
    FOREIGN KEY(session_id) REFERENCES script_sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS script_logout_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    player_uid TEXT NOT NULL,
    logout_time TEXT,
    event_type TEXT NOT NULL,
    FOREIGN KEY(session_id) REFERENCES script_sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS script_persistence_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    persistence_event TEXT NOT NULL,
    FOREIGN KEY(session_id) REFERENCES script_sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS script_errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    error_type TEXT NOT NULL,
    error_text TEXT NOT NULL,
    FOREIGN KEY(session_id) REFERENCES script_sessions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_event_child_type
ON economy_event_children(child_type);

CREATE INDEX IF NOT EXISTS idx_player_actions_player
ON player_actions(player_id);

CREATE INDEX IF NOT EXISTS idx_player_sessions_time
ON player_sessions(connect_time);

CREATE INDEX IF NOT EXISTS idx_territory_zone_type
ON territory_zones(zone_type_id);

CREATE INDEX IF NOT EXISTS idx_territory_position
ON territory_zones(pos_x,pos_z);

CREATE INDEX IF NOT EXISTS idx_cluster_position
ON cluster_instances(pos_x,pos_z);

CREATE INDEX IF NOT EXISTS idx_map_object_position
ON map_objects(pos_x,pos_z);

CREATE INDEX IF NOT EXISTS idx_script_logout_uid
ON script_logout_events(player_uid);
