# Current State Report — DayZ Sentinel

> Erstellt auf Basis des vorhandenen Quellcodes (Stand: 2026-06-17).  
> Keine externen Quellen verwendet.

---

## 1. Was funktioniert bereits

### FastAPI-Backend
- **App-Bootstrapping** vollständig: `sentinel_spr019/api/main.py` startet FastAPI, bindet zwei Router ein und stellt `GET /api/v1/health` bereit.
- **Economy-Items-API** (vollständig nutzbar):
  - `GET /api/v1/economy/items` – paginierte Liste aller Items (limit/offset/search)
  - `GET /api/v1/economy/items/{item_name}` – Item nach Name, 404 wenn nicht vorhanden
  - `GET /api/v1/economy/items/stats/count` – Gesamtanzahl Items
- **Economy-Events-API** (vollständig nutzbar):
  - `GET /api/v1/economy/events` – paginierte Liste aller Events (limit/offset/active_only/search)
  - `GET /api/v1/economy/events/{event_name}` – Event nach Name, 404 wenn nicht vorhanden
  - `POST /api/v1/economy/events/{event_name}/toggle-active` – aktiv/inaktiv schalten
  - `GET /api/v1/economy/events/stats/count` – Gesamtanzahl Events (optional active_only)
- **SQLite-Datenbankanbindung**: `api/database.py` liefert Verbindungen auf die persistente `sentinel.db`.
- **Repository-Schicht**: Klassen `EconomyItemsRepository` und `EconomyEventsRepository` mit Methoden `get_all`, `get_by_name`, `search`, `get_count` (Events zusätzlich `toggle_active`).
- **Pydantic-Modelle**: `EconomyItem`, `EconomyItemResponse`, `EconomyEvent`, `EconomyEventResponse` vollständig definiert.
- **Events-Importer**: `importer/economy/events_importer.py` liest `events.xml` und befüllt `economy_events`.
- **Docker-Deployment**: `Dockerfile` und `docker-compose.yml` lauffähig; DB-Datei wird als Volume gemountet.
- **Integrations-Testskript**: `scripts/test_api.py` testet alle Endpunkte gegen eine laufende API-Instanz.

### Datenbankschema (definiert, nicht vollständig migriert)
- Schema `sentinel_v1_schema.sql` (REV-1) definiert 25 Tabellen für Items, Events, Karten, Spieler, Server-Logs.
- Schema `sentinel_v1_schema_rev2.sql` (REV-2) ergänzt Import-Tracking, Log-Ereignisse und fehlende Indizes.

---

## 2. Was ist teilweise implementiert

| Komponente | Stand | Lücke |
|---|---|---|
| **types.xml-Importer** | `test_import_run.py` referenziert `importer.economy.types_importer.import_types` | `types_importer.py` existiert nicht; Import schlägt fehl |
| **Pydantic-Response-Modelle** | Modelle definiert, aber Routen verwenden `response_model=dict` statt der typisierten Klassen | API-Dokumentation (Swagger) zeigt keine Feldtypen |
| **Suchfunktion (offset)** | Route akzeptiert `offset`-Parameter, `search()`-Methoden ignorieren ihn | Paginierung bei Suche fehlt |
| **Schema-Konsistenz** | Zwei SQL-Schema-Dateien vorhanden, aber reale DB-Spalten weichen ab (`item_name` vs. `name`, `min_count` vs. `min_value`, `max_count` vs. `max_value`) | Kein Migrations-Runner; Schema und Produktiv-DB divergieren |
| **Tote Repository-Klasse** | `api/repositories/economy_repository.py` (`EconomyRepository`) dupliziert Funktionalität | Nicht eingebunden, nie verwendet |
| **CORS** | Keine Middleware konfiguriert | Frontend-Zugriff aus Browsern blockiert |
| **Fehler-Handling** | `detail=str(e)` gibt interne Fehlerdetails im HTTP-Response zurück | Sicherheitslücke: Stack-Traces/DB-Pfade potenziell sichtbar |

---

## 3. Was fehlt für eine erste nutzbare Version

| # | Fehlendes Element | Begründung |
|---|---|---|
| 1 | `types_importer.py` (Items aus `types.xml` importieren) | Ohne ihn ist die `economy_items`-Tabelle leer; alle Item-Endpunkte liefern leere Ergebnisse |
| 2 | API-Key-Authentifizierung für Schreib-Endpunkte (POST/PUT/DELETE) | `toggle-active` ist ungeschützt; jeder kann Events deaktivieren |
| 3 | Generische 500-Fehlermeldungen + Server-seitiges Logging | `str(e)` in HTTP-Antworten gibt interne Pfade und DB-Fehlermeldungen preis |
| 4 | Parameterized Queries in `economy_events_repository.py` | f-String-Interpolation in SQL-Statements (Zeilen 30, 36–44, 107–114, 130) ist SQL-Injection-Angriffsfläche |
| 5 | `requests` in `requirements.txt` | `scripts/test_api.py` importiert `requests`; `pip install -r requirements.txt` allein reicht nicht |

---

## 4. Die 5 wichtigsten nächsten Arbeitsschritte

### Schritt 1 — SQL-Injection-Lücke schließen (Sicherheit)
Alle f-String-SQL-Interpolationen in `economy_events_repository.py` durch Parameterized Queries mit `?`-Platzhaltern ersetzen.

**Aufwand:** ~1–2 Stunden  
**Betroffene Dateien:**
- `sentinel_spr019/api/repositories/economy_events_repository.py` (Zeilen 30, 36–44, 107–114, 130)

---

### Schritt 2 — Fehler-Handling absichern (Sicherheit)
`detail=str(e)` in allen Route-Handlern durch generische Meldungen ersetzen; Fehler serverseitig mit Python-`logging` erfassen.

**Aufwand:** ~2–3 Stunden  
**Betroffene Dateien:**
- `sentinel_spr019/api/routes/economy_items.py`
- `sentinel_spr019/api/routes/economy_events.py`
- `sentinel_spr019/api/main.py` (Logging-Konfiguration)

---

### Schritt 3 — `types_importer.py` implementieren (Kernfunktion)
Analogen Importer zu `events_importer.py` für `types.xml` erstellen; `test_import_run.py`-Import-Pfad korrigieren. Ohne ihn sind Item-Endpunkte nutzlos.

**Aufwand:** ~3–4 Stunden  
**Betroffene Dateien:**
- `sentinel_spr019/importer/economy/types_importer.py` (neu anlegen)
- `sentinel_spr019/scripts/test_import_run.py` (Import-Pfad korrigieren)

---

### Schritt 4 — API-Key-Schutz für Schreib-Endpunkte (Sicherheit)
FastAPI-Dependency mit HTTP-Header-Prüfung (`X-API-Key`) für alle POST/PUT/DELETE-Routen; Key aus `.env`-Datei laden.

**Aufwand:** ~2–3 Stunden  
**Betroffene Dateien:**
- `sentinel_spr019/api/main.py` oder neues `sentinel_spr019/api/dependencies.py` (neu anlegen)
- `sentinel_spr019/api/routes/economy_events.py`
- `.env.example`

---

### Schritt 5 — Schema-Konsistenz herstellen und `requests` ergänzen (Stabilität)
Spaltenbezeichnungen in `sentinel_v1_schema.sql` an die reale DB angleichen (`item_name`→`name`, `min_count`/`max_count`→`min_value`/`max_value`); `requests` in `requirements.txt` aufnehmen.

**Aufwand:** ~1–2 Stunden  
**Betroffene Dateien:**
- `sentinel_spr019/database/schema/sentinel_v1_schema.sql`
- `requirements.txt`

---

## 5. Zusammenfassung: Aufwand pro Arbeitsschritt

| Schritt | Beschreibung | Aufwand |
|---|---|---|
| 1 | SQL-Injection schließen | 1–2 h |
| 2 | Fehler-Handling absichern | 2–3 h |
| 3 | `types_importer.py` implementieren | 3–4 h |
| 4 | API-Key-Authentifizierung | 2–3 h |
| 5 | Schema-Konsistenz + `requirements.txt` | 1–2 h |
| **Gesamt** | | **~9–14 h** |

---

*Bericht basiert ausschließlich auf dem vorhandenen Quellcode im Repository.*
