# Copilot Audits — Index

Automated and manual audit reports for DayZ Sentinel.

---

## Reports

| File | Type | Date | Status |
|------|------|------|--------|
| [`full_project_audit.md`](./full_project_audit.md) | Full project analysis | 2026-06-17 | ✅ Complete |
| [`security_audit.md`](./security_audit.md) | Security-focused audit | 2026-06-17 | ✅ Complete |
| [`architecture_audit.md`](./architecture_audit.md) | Architecture review | 2026-06-17 | ✅ Complete |
| [`code_quality_audit.md`](./code_quality_audit.md) | Code quality review | 2026-06-17 | ✅ Complete |

---

## Summary of Open Issues

| ID | Severity | Summary |
|----|----------|---------|
| AUDIT-001 | 🔴 Critical | No auth on `toggle-active` POST endpoint |
| AUDIT-002 | 🔴 Critical | Internal error details in HTTP 500 responses |
| AUDIT-003 | 🟠 High | DB connection leaks (no context manager) |
| AUDIT-004 | 🟠 High | f-String SQL interpolation |
| AUDIT-005 | 🟠 High | `.env` / `API_PORT` never read |
| AUDIT-006 | 🟡 Medium | `dict_factory` duplicated in two files |
| AUDIT-007 | 🟡 Medium | Dead code in repository layer |
| AUDIT-008 | 🟡 Medium | `requests` missing from `requirements.txt` |
| AUDIT-009 | 🟡 Medium | Broken import in `test_import_run.py` |
| AUDIT-010 | 🟡 Medium | `offset` ignored in search endpoints |
| AUDIT-011 | 🟡 Medium | Package name contains sprint number |
| AUDIT-012 | 🔵 Low | No CORS middleware |
| AUDIT-013 | 🔵 Low | README contains incorrect endpoint docs |

---

*Last updated: 2026-06-17*
