# Data Pipeline Status — DayZ Sentinel

> Audit date: 2026-06-18  
> Scope: alle bekannten Datenquellen im Repository (`sentinel_spr019/`)

---

## Übersicht

| Datenquelle          | Importer | Tests | DB-Tabellen | API   | Vollständig nutzbar |
|----------------------|----------|-------|-------------|-------|---------------------|
| ADM Logs             | ❌ Nein  | ❌ Nein | ✅ Ja (10+) | ❌ Nein | ❌ Nein |
| types.xml            | ✅ Ja    | ✅ Ja   | ✅ Ja (10)  | ✅ Ja   | ✅ **Ja** |
| events.xml           | ⚠️ Teilweise | ❌ Nein | ✅ Ja (4)  | ✅ Ja   | ⚠️ Teilweise |
| cfgeventspawns.xml   | ❌ Nein  | ❌ Nein | ❌ Nein     | ❌ Nein | ❌ Nein |
| Trader Daten         | ❌ Nein  | ❌ Nein | ❌ Nein     | ❌ Nein | ❌ Nein |
| Nitrado API          | ❌ Nein  | ❌ Nein | ❌ Nein     | ❌ Nein | ❌ Nein |

---

## Detailanalyse

### 1. ADM Logs

DayZ-Serverlogdateien (`*.ADM`) enthalten Spieler-Verbindungen, Positionsdaten, Schadensevents und Serverstart-Informationen.

| Kriterium        | Status | Details |
|------------------|--------|---------|
| Importer         | ❌ Nein | Kein Log-Parser vorhanden |
| Tests            | ❌ Nein | — |
| DB-Tabellen      | ✅ Ja   | `players`, `player_sessions`, `player_positions`, `player_damage_events`, `player_actions`, `server_sessions` (schema v1) + `script_sessions`, `script_engine_events`, `script_logout_events`, `script_persistence_events`, `script_errors`, `network_events`, `localization_errors` (schema rev2) |
| API              | ❌ Nein | Keine API-Routen für Player-Daten |
| Vollständig      | ❌ Nein | Schema definiert, aber kein Code befüllt diese Tabellen |

**Befund:** Das Datenbankschema ist umfangreich vorbereitet (13+ Tabellen), aber die gesamte Ingestion-Pipeline fehlt vollständig.

---

### 2. types.xml

DayZ Economy-Konfigurationsdatei für Item-Spawns (Loot).

| Kriterium        | Status | Details |
|------------------|--------|---------|
| Importer         | ✅ Ja   | `sentinel_spr019/importer/economy/types_importer.py` — Upsert-Logik, Schema-Migration, Foreign-Key-Handling |
| Tests            | ✅ Ja   | `tests/test_types_importer.py` — 11 Testklassen, ≥25 Testfälle (Insert, Upsert, Flags, Categories, Usages, Values, Tags, Transaktionen, Migration) |
| DB-Tabellen      | ✅ Ja   | `economy_items`, `economy_item_flags`, `economy_categories`, `economy_item_categories`, `economy_usages`, `economy_item_usages`, `economy_values`, `economy_item_values`, `economy_tags`, `economy_item_tags` |
| API              | ✅ Ja   | `GET /api/v1/economy/items`, `GET /api/v1/economy/items/{name}`, `GET /api/v1/economy/items/stats/count` |
| Vollständig      | ✅ **Ja** | Vollständig implementiert und getestet |

---

### 3. events.xml

DayZ Economy-Konfigurationsdatei für Spawn-Events (Fahrzeuge, Helikopter-Abstürze etc.).

| Kriterium        | Status | Details |
|------------------|--------|---------|
| Importer         | ⚠️ Teilweise | `sentinel_spr019/importer/economy/events_importer.py` — nur `INSERT`, kein Upsert; schlägt bei Re-Import mit `IntegrityError` still fehl (skipped statt update); keine Befüllung von `economy_event_flags`, `economy_event_secondary`, `economy_event_children` |
| Tests            | ❌ Nein | Kein Test für den Events-Importer |
| DB-Tabellen      | ✅ Ja   | `economy_events`, `economy_event_flags`, `economy_event_secondary`, `economy_event_children` |
| API              | ✅ Ja   | `GET /api/v1/economy/events`, `GET /api/v1/economy/events/{name}`, `POST /api/v1/economy/events/{name}/toggle-active`, `GET /api/v1/economy/events/stats/count` |
| Vollständig      | ⚠️ Teilweise | API und Haupttabelle funktionieren; Importer ist nicht produktionsreif (kein Upsert, keine Subtabellen, keine Tests) |

**Befund:** API ist vollständig, aber der Importer fehlt Upsert-Logik und befüllt 3 von 4 event-bezogenen Tabellen nicht.

---

### 4. cfgeventspawns.xml

Definiert konkrete Spawn-Koordinaten für Events auf der Karte.

| Kriterium        | Status | Details |
|------------------|--------|---------|
| Importer         | ❌ Nein | Nicht vorhanden |
| Tests            | ❌ Nein | — |
| DB-Tabellen      | ❌ Nein | Keine dedizierten Tabellen; potenziell verwandt: `group_points`, `group_prototypes`, `cluster_instances` (schema v1), aber keine direkte Zuordnung |
| API              | ❌ Nein | — |
| Vollständig      | ❌ Nein | Vollständig fehlend |

---

### 5. Trader Daten

Trader-Konfigurationen (z. B. TraderConfig.txt oder JSON aus Expansion/Dr. Jones Trader Mod).

| Kriterium        | Status | Details |
|------------------|--------|---------|
| Importer         | ❌ Nein | Nicht vorhanden |
| Tests            | ❌ Nein | — |
| DB-Tabellen      | ❌ Nein | Keine Tabellen vorhanden |
| API              | ❌ Nein | — |
| Vollständig      | ❌ Nein | Vollständig fehlend |

---

### 6. Nitrado API

REST-API des Hosting-Anbieters Nitrado für Server-Management (RCON, Datei-Zugriff, Serversteuerung).

| Kriterium        | Status | Details |
|------------------|--------|---------|
| Importer / Client | ❌ Nein | Kein HTTP-Client oder Wrapper vorhanden |
| Tests            | ❌ Nein | — |
| DB-Tabellen      | ❌ Nein | Keine Tabellen vorhanden |
| API (intern)     | ❌ Nein | Keine internen Routen, die Nitrado proxyen |
| Vollständig      | ❌ Nein | Vollständig fehlend |

---

## Größte funktionale Lücke

**→ ADM Log Pipeline**

Das Datenbankschema enthält **13 Tabellen** für Spieler-, Positions-, Schadens- und Server-Daten — die umfangreichste Datenstruktur im gesamten Projekt. Dennoch existiert **kein einziger Zeile produktiven Code**, der diese Tabellen befüllt:

- Kein Log-Parser / Importer
- Keine Tests
- Keine API-Routen für Player-Analytics

Die ADM-Logs sind die **primäre Echtzeitdatenquelle** eines DayZ-Servers. Ohne sie ist Sentinel im Kern ein reines Economy-Konfigurations-Tool — kein Server-Monitoring- oder Analytics-System, wie es das README und die Roadmap beschreiben.

**Empfehlung:** ADM Log Importer als nächstes Sprint-Ziel priorisieren:
1. Log-Parser für `players`, `player_sessions`, `player_positions`
2. Log-Parser für `player_damage_events`, `player_actions`
3. Log-Parser für `server_sessions`
4. API-Routen `/api/v1/players` und `/api/v1/server/sessions`
5. Tests für alle Parser

---

*Generiert von Copilot Agent — Sprint SPR-019 Audit*
