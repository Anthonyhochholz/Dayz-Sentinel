# Roadmap — DayZ Sentinel

> Nur zukünftige Arbeiten. Aktueller Zustand steht in `docs/PROJECT_MEMORY.md`.

## P1 — Stabilität, Sicherheit, Maintainability

| ID | Task | Why it matters |
|----|------|----------------|
| P1-003b | Dependency-Updates automatisieren (Dependabot/Renovate) | Die Versionen sind gepinnt, aber niemand hebt sie planmäßig an |
| P1-005 | Linting und Formatierung in CI erzwingen (ruff) | Konsistenter Stil, ohne ihn im Review von Hand zu prüfen |
| P1-006 | Breite `except Exception`-Blöcke in den Routen verschlanken | Sie verdecken derzeit jeden Repository-Fehler als generischen 500er |

## P2 — Ingestion-Erweiterung

| ID | Task | Why it matters |
|----|------|----------------|
| P2-001 | RPT-Importer implementieren | Aktuell werden RPT-Dateien nur erkannt, nicht importiert |
| P2-002 | Cluster- und World-Importer implementieren | Aktiviert bestehende Schema-Domänen außerhalb Economy |
| P2-004 | Import-Tracking um Retry-/Reprocessing-Strategien ergänzen | Kontrollierte Wiederholbarkeit bei Teilfehlern |
| P2-005 | Scheduler für wiederkehrende Mirror-Importe | Die CLI existiert, wird aber noch von Hand ausgelöst |

## P3 — Plattformreife

| ID | Task | Why it matters |
|----|------|----------------|
| P3-001 | Analytics-/Read-Model-Layer aufbauen | Aus Rohdaten verwertbare Server-Insights ableiten |
| P3-003 | Paketnamen von `sentinel_spr019` auf stabilen Namen migrieren | Technische Schulden durch sprint-gekoppelten Namespace reduzieren |
| P3-004 | Observability ausbauen (Health+, Metriken, Logging-Standards) | Bessere Betriebsfähigkeit im produktiven Betrieb |
| P3-005 | SQLite-Zugriff auf WAL und Verbindungs-Reuse umstellen | Aktuell öffnet jeder Request eine eigene Verbindung |

## Recently Completed

Diese Einträge sind erledigt; Details stehen in `docs/CHANGELOG.md`.

| ID | Task |
|----|------|
| P1-001 | Cross-Layer-Abhängigkeit aufgelöst (`persistence`-Schicht) |
| P1-002 | CI-Workflow eingeführt |
| P1-003 | Dependencies gepinnt, Runtime und Dev getrennt |
| P1-004 | Alle Endpunkte auf typisierte `response_model` umgestellt |
| P2-003 | Import-CLI (`python -m sentinel_spr019.importer`) |
| P3-002 | CORS-Konfiguration via `SENTINEL_CORS_ORIGINS` |

## Future Ideas

- PostgreSQL-Backend als Option
- Realtime-Log-Streaming
- Discord-/Webhook-Benachrichtigungen
- Map-Visualisierung für Cluster/World-Daten
