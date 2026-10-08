# AcademicIQ Runbook

**Audience:** System administrators and operators  
**Version:** 1.0

---

## 1. Starting the System

### Development (one command)
```bash
docker compose up
```

### With local LLM (Ollama)
```bash
docker compose --profile ai up
# Then pull a model:
docker exec academiciq-ollama-1 ollama pull llama3
```

### Production
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## 2. Running Migrations

```bash
# Apply all pending migrations
docker compose exec backend alembic upgrade head

# Check current migration state
docker compose exec backend alembic current

# Generate a new migration after model changes
docker compose exec backend alembic revision --autogenerate -m "description"
```

**Never run destructive migrations (`--drop-all`, `alembic downgrade`) without explicit approval and a verified backup.**

---

## 3. Seeding Demo Data

```bash
docker compose exec backend python scripts/seed.py
```

Creates 60 synthetic students, 4 semesters of results, all roles. **SYNTHETIC DATA only.**

---

## 4. Running Tests

```bash
# Full backend test suite
docker compose exec backend pytest tests/ -v --tb=short

# RBAC matrix only (fast)
docker compose exec backend pytest tests/rbac/ -v

# Frontend tests
docker compose exec frontend npm run test -- --run
```

---

## 5. Uploading a Result PDF

1. Log in as Admin.
2. Navigate to Results → Upload Results.
3. Select the PDF (max 50 MB, PDF only).
4. Wait for background processing (status: QUEUED → PROCESSING → READY_FOR_REVIEW).
5. Review the validation preview (valid/warning/error/unmatched counts).
6. Fix or skip records as needed.
7. Click "Commit" to write valid records to the official table.
8. A new upload version is recorded; prior versions remain queryable.

---

## 6. Monitoring Background Jobs

- Flower UI: http://localhost:5555
- Check worker health: `docker compose exec celery_worker celery -A app.celery_app inspect ping`
- View active tasks: `docker compose exec celery_worker celery -A app.celery_app inspect active`

---

## 7. Log Access

```bash
# Backend structured JSON logs
docker compose logs backend --follow

# Celery worker logs
docker compose logs celery_worker --follow

# Filter by upload_id
docker compose logs backend | Select-String "upload_id=<UUID>"
```

---

## 8. Database Backup and Restore

```bash
# Backup
docker compose exec db pg_dump -U academiciq academiciq > backup_$(Get-Date -Format "yyyyMMdd_HHmmss").sql

# Restore (stop app first)
docker compose stop backend celery_worker
docker compose exec -T db psql -U academiciq academiciq < backup_20260101_120000.sql
docker compose start backend celery_worker
```

**Retention policy:** Academic records must be retained per institutional regulations (default: 7 years). Backup files should be encrypted at rest. Automated nightly backup is recommended.

---

## 9. Health Checks

```bash
# API health
curl http://localhost:8000/health

# Readiness (DB connectivity)
curl http://localhost:8000/ready

# Expected responses
# /health  → {"status":"ok","app":"AcademicIQ","version":"1.0.0"}
# /ready   → {"status":"ready"}
```

---

## 10. Adding a University-Specific Parser

1. Create `backend/app/parsers/<university_name>_parser.py`
2. Subclass `BaseParser`, implement `can_parse()` and `extract()`
3. Add to `PLUGIN_PARSERS` list in `backend/app/parsers/plugins.py`
4. Add golden test PDFs to `backend/tests/golden/<university>/`
5. Write `tests/unit/test_<university>_parser.py` with golden-file assertions
6. Run parser tests: `pytest tests/unit/test_<university>_parser.py -v`
7. H1 accuracy must be ≥ 98% before the parser is committed to main

---

## 11. Changing the LLM Provider

Edit `.env` (or environment variables in Docker Compose):

```env
# Local Ollama (default — no student data leaves institution)
LLM_PROVIDER=local
LLM_BASE_URL=http://ollama:11434
LLM_MODEL=llama3

# OpenAI (pseudonymized payload only — see ADR-006)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

---

## 12. Common Issues

| Symptom | Cause | Fix |
|---|---|---|
| Upload stuck at QUEUED | Celery worker not running | `docker compose up celery_worker` |
| Upload status FAILED | Parser error or file corrupt | Check `result_processing_logs` table |
| Login 423 Locked | Too many failed attempts | Admin: clear `locked_until` in `users` table |
| AI Insights empty | No verified metrics | Compute analytics first via `/analytics/student/{id}` |
| ML disabled message | Insufficient data | Normal — need ≥500 records, ≥3 semesters |
| Frontend 401 loop | Expired refresh token | Clear localStorage, log in again |

---

## 13. Security Notes

- `SECRET_KEY` must be ≥64 random hex characters in production: `openssl rand -hex 64`
- Database password must be changed from the default before any real data is loaded
- `UPLOAD_DIR` must be outside the web root (already is in Docker config)
- Audit logs are append-only — never run `DELETE` or `UPDATE` on `audit_logs` table
- Rate limiting is active on `/auth/*`, `/results/upload`, and `/ai/*` endpoints

---

## 14. Data Deletion and Erasure (DPDP Act 2023)

1. Receive a verified erasure request.
2. Soft-delete the student record (`is_deleted=True`).
3. Anonymize PII fields (name, register number) with a hash.
4. Log the erasure action in `audit_logs` with action=`DATA_ERASURE`.
5. Retain: result records (for institutional compliance), with student reference replaced by anonymized token.
6. Document: retention schedule exception (educational records — 7 years minimum).

*Full erasure workflow requires legal review per your institution's data governance policy.*
