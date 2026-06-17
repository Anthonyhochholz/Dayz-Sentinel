
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS economy_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    nominal INTEGER,
    lifetime INTEGER,
    restock INTEGER,
    min_value INTEGER,
    max_value INTEGER
);

CREATE TABLE IF NOT EXISTS economy_item_flags (
    item_id INTEGER PRIMARY KEY,
    count_in_cargo INTEGER,
    count_in_hoarder INTEGER,
    count_in_map INTEGER,
    count_in_player INTEGER,
    crafted INTEGER,
    deloot INTEGER,
    FOREIGN KEY(item_id) REFERENCES economy_items(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS economy_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS economy_item_categories (
    item_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    PRIMARY KEY(item_id, category_id),
    FOREIGN KEY(item_id) REFERENCES economy_items(id) ON DELETE CASCADE,
    FOREIGN KEY(category_id) REFERENCES economy_categories(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS economy_usages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS economy_item_usages (
    item_id INTEGER NOT NULL,
    usage_id INTEGER NOT NULL,
    PRIMARY KEY(item_id, usage_id),
    FOREIGN KEY(item_id) REFERENCES economy_items(id) ON DELETE CASCADE,
    FOREIGN KEY(usage_id) REFERENCES economy_usages(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS economy_values (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS economy_item_values (
    item_id INTEGER NOT NULL,
    value_id INTEGER NOT NULL,
    PRIMARY KEY(item_id, value_id),
    FOREIGN KEY(item_id) REFERENCES economy_items(id) ON DELETE CASCADE,
    FOREIGN KEY(value_id) REFERENCES economy_values(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS economy_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS economy_item_tags (
    item_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY(item_id, tag_id),
    FOREIGN KEY(item_id) REFERENCES economy_items(id) ON DELETE CASCADE,
    FOREIGN KEY(tag_id) REFERENCES economy_tags(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS economy_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_name TEXT NOT NULL UNIQUE,
    nominal INTEGER,
    min_count INTEGER,
    max_count INTEGER,
    lifetime INTEGER,
    restock INTEGER,
    saferadius REAL,
    distanceradius REAL,
    cleanupradius REAL,
    position_mode TEXT,
    limit_mode TEXT,
    active INTEGER
);

CREATE TABLE IF NOT EXISTS economy_event_flags (
    event_id INTEGER PRIMARY KEY,
    deletable INTEGER,
    init_random INTEGER,
    remove_damaged INTEGER,
    FOREIGN KEY(event_id) REFERENCES economy_events(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS economy_event_secondary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    secondary_name TEXT NOT NULL,
    FOREIGN KEY(event_id) REFERENCES economy_events(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS economy_event_children (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    child_type TEXT NOT NULL,
    min_count INTEGER,
    max_count INTEGER,
    lootmin INTEGER,
    lootmax INTEGER,
    FOREIGN KEY(event_id) REFERENCES economy_events(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS group_prototypes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS group_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS group_prototype_categories (
    group_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    PRIMARY KEY(group_id, category_id)
);

CREATE TABLE IF NOT EXISTS group_usages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS group_prototype_usages (
    group_id INTEGER NOT NULL,
    usage_id INTEGER NOT NULL,
    PRIMARY KEY(group_id, usage_id)
);

CREATE TABLE IF NOT EXISTS group_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS group_prototype_tags (
    group_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY(group_id, tag_id)
);

CREATE TABLE IF NOT EXISTS group_points (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    pos_x REAL,pos_y REAL,pos_z REAL,
    point_range REAL,
    point_height REAL
);

CREATE TABLE IF NOT EXISTS group_proxies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    proxy_type TEXT,
    pos_x REAL,pos_y REAL,pos_z REAL,
    roll REAL,pitch REAL,yaw REAL
);

CREATE TABLE IF NOT EXISTS cluster_instances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cluster_name TEXT NOT NULL,
    pos_x REAL,pos_y REAL,pos_z REAL,
    angle REAL,
    source_file TEXT
);

CREATE TABLE IF NOT EXISTS map_objects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_name TEXT NOT NULL,
    pos_x REAL,pos_y REAL,pos_z REAL,
    roll REAL,pitch REAL,yaw REAL,
    angle REAL
);

CREATE TABLE IF NOT EXISTS territory_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file TEXT NOT NULL UNIQUE,
    territory_category TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS territories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    territory_file_id INTEGER NOT NULL,
    color INTEGER
);

CREATE TABLE IF NOT EXISTS territory_zone_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zone_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS territory_zones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    territory_id INTEGER NOT NULL,
    zone_type_id INTEGER NOT NULL,
    pos_x REAL,
    pos_z REAL,
    radius REAL,
    smin INTEGER,smax INTEGER,dmin INTEGER,dmax INTEGER
);

CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_uid TEXT NOT NULL UNIQUE,
    player_name TEXT
);

CREATE TABLE IF NOT EXISTS player_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    connect_time TEXT,
    disconnect_time TEXT
);

CREATE TABLE IF NOT EXISTS player_positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    pos_x REAL,pos_y REAL,pos_z REAL
);

CREATE TABLE IF NOT EXISTS player_damage_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    timestamp TEXT,
    hp_before REAL,
    source TEXT,
    bodypart TEXT,
    damage REAL,
    weapon TEXT,
    pos_x REAL,pos_y REAL,pos_z REAL
);

CREATE TABLE IF NOT EXISTS player_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    timestamp TEXT,
    action_name TEXT,
    item_name TEXT
);

CREATE TABLE IF NOT EXISTS server_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time TEXT,
    version TEXT,
    executable TEXT
);

CREATE INDEX idx_players_uid ON players(player_uid);
CREATE INDEX idx_player_positions_time ON player_positions(player_id,timestamp);
CREATE INDEX idx_damage_time ON player_damage_events(player_id,timestamp);
CREATE INDEX idx_cluster_name ON cluster_instances(cluster_name);
CREATE INDEX idx_map_object_name ON map_objects(object_name);
