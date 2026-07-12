# Roadmap — DayZ Sentinel

> Future work only. Aktueller Zustand steht in `docs/PROJECT_MEMORY.md`.

## P1 — Stabilität, Sicherheit, Maintainability

| ID | Task | Why it matters |
|----|------|----------------|
| P1-001 | Cross-Layer-Abhängigkeit auflösen (`import_pipeline` -> `api.repositories`) | Saubere Architekturgrenzen zwischen Importer- und API-Layer |
| P1-002 | CI-Workflow für `python -m pytest -q tests/` einführen | Kontinuierliche Qualitätssicherung statt nur lokaler Testläufe |
| P1-003 | Dependencies pinnen und regelmäßige Security-Updates etablieren | Reproduzierbare Builds + geringeres Sicherheitsrisiko |
| P1-004 | API-Responses auf typed `response_model` umstellen | Stabilere API-Verträge und bessere OpenAPI-Qualität |

## P2 — Ingestion-Erweiterung

| ID | Task | Why it matters |
|----|------|----------------|
| P2-001 | RPT-Importer implementieren | Aktuell werden RPT-Dateien nur erkannt, nicht importiert |
| P2-002 | Cluster- und World-Importer implementieren | Aktiviert bestehende Schema-Domänen außerhalb Economy |
| P2-003 | Import-Pipeline als CLI/Job-Entry-Point bereitstellen | Operativer Mirror-Import ohne direkten Python-Aufruf |
| P2-004 | Import-Tracking um Retry-/Reprocessing-Strategien ergänzen | Kontrollierte Wiederholbarkeit bei Teilfehlern |

## P3 — Plattformreife

| ID | Task | Why it matters |
|----|------|----------------|
| P3-001 | Analytics-/Read-Model-Layer aufbauen | Aus Rohdaten verwertbare Server-Insights ableiten |
| P3-002 | Browser-fähige CORS-Konfiguration einführen | Voraussetzung für Dashboard-/Frontend-Anbindung |
| P3-003 | Paketnamen von `sentinel_spr019` auf stabilen Namen migrieren | Technische Schulden durch sprint-gekoppelten Namespace reduzieren |
| P3-004 | Observability ausbauen (Health+, Metriken, Logging-Standards) | Bessere Betriebsfähigkeit im produktiven Betrieb |

## Future Ideas

- PostgreSQL-Backend als Option
- Realtime-Log-Streaming
- Discord-/Webhook-Benachrichtigungen
- Map-Visualisierung für Cluster/World-Daten
