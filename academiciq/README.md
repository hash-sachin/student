# AcademicIQ

**Evidence-Driven Explainable Academic Intelligence and Early-Warning Platform for Longitudinal University Result Analytics**

> "AcademicIQ transforms heterogeneous university result PDFs into longitudinal, explainable, evidence-driven academic intelligence that helps faculty identify performance changes, understand why students may need academic attention, evaluate hypothetical improvement scenarios, and make better-informed academic decisions."

---

## Quick Start (one command)

```bash
docker compose up
```

Then open:
- **Frontend**: http://localhost:5173
- **API docs**: http://localhost:8000/api/docs
- **Flower (job monitor)**: http://localhost:5555

Default credentials (seed data — change in production):
| Role | Email | Password |
|---|---|---|
| Admin | admin@academiciq.edu | Admin@123! |
| Faculty | faculty@academiciq.edu | Faculty@123! |
| HOD | hod@academiciq.edu | Hod@123! |
| Student | student1@academiciq.edu | Student@123! |

---

## Project Structure

```
academiciq/
├── backend/                  # FastAPI Python backend
│   ├── app/
│   │   ├── core/             # Config, security, logging, middleware, exceptions
│   │   ├── auth/             # JWT auth, RBAC, dependencies
│   │   ├── users/            # User management
│   │   ├── students/         # Student master
│   │   ├── academics/        # Departments, programs, batches, grading schemes
│   │   ├── results/          # Upload, pipeline, staging, commit
│   │   ├── parsers/          # PDF parser interface + GenericPDF + OCR + plugins
│   │   ├── validation/       # Extraction validation engine
│   │   ├── analytics/        # L1 deterministic analytics engine
│   │   ├── profile/          # Longitudinal Academic Profile service
│   │   ├── intelligence/     # Academic Attention Engine v1.0
│   │   ├── evidence/         # Evidence graph (nodes + edges)
│   │   ├── interventions/    # Intervention rules + workflow
│   │   ├── simulation/       # What-If simulation engine
│   │   ├── ai/               # AI insight service + guardrails
│   │   ├── ml/               # Optional ML layer (gated)
│   │   ├── reports/          # PDF/Excel/CSV report generator
│   │   ├── audit/            # Append-only audit log
│   │   ├── notifications/    # User notifications
│   │   ├── evaluation/       # H1–H8 hypothesis evaluation framework
│   │   └── database/         # SQLAlchemy models, session, base
│   ├── alembic/              # Database migrations
│   ├── scripts/seed.py       # Demo seed (SYNTHETIC DATA)
│   └── tests/                # pytest: unit, integration, API, RBAC, golden
├── frontend/                 # React + TypeScript + Vite + Tailwind
│   └── src/
│       ├── api/              # Axios client + typed endpoints
│       ├── hooks/            # useAuth, useStudents, useProfile, useAttention
│       ├── layouts/          # MainLayout (sidebar nav, WCAG skip-link)
│       ├── pages/            # All page components by feature
│       ├── components/       # MetricBadge, HypotheticalBanner, AttentionBadge, etc.
│       ├── charts/           # SemesterTrendChart, GradeDistributionChart (accessible)
│       ├── types/            # TypeScript types
│       └── test/             # Vitest component tests
├── docs/
│   ├── decisions/            # Architecture Decision Records (ADR-001 to ADR-010)
│   ├── security/             # STRIDE threat model, privacy notice
│   └── evaluation/           # H7 usability study template
├── tests/e2e/                # Playwright end-to-end tests
└── .github/workflows/ci.yml  # GitHub Actions CI
```

---

## Architecture: Three Intelligence Layers

```
Layer 1 — Deterministic Analytics (always active)
  → All statistics, comparisons, attention scores
  → Reproducible: same inputs + algorithm version = same output
  → Label: CALCULATED or ESTIMATED

Layer 2 — Machine Learning (gated — Section 10)
  → Activates only when: ≥500 records, ≥3 semesters, ≥50 positive class
  → Temporal splits only. Beats baselines or stays disabled.
  → Label: ESTIMATED

Layer 3 — Generative AI (explains verified facts only)
  → Input: verified metrics payload (pseudonymized)
  → 5 programmatic guardrails before any output is stored
  → Never invents data. Falls back to deterministic template on failure.
  → Label: ESTIMATED
```

## Metric Label Taxonomy

Every number displayed anywhere carries exactly one label:

| Label | Meaning |
|---|---|
| **OFFICIAL** | Extracted directly from the source PDF |
| **CALCULATED** | Derived deterministically from official data |
| **ESTIMATED** | Heuristic or model output (attention score, AI text) |
| **HYPOTHETICAL** | What-if simulation output only — never an actual result |

---

## Running Tests

```bash
# Backend
cd backend
pip install -e ".[dev]"
pytest tests/ -v

# RBAC matrix only
pytest tests/rbac/ -v

# Frontend
cd frontend
npm ci
npm run test -- --run
```

---

## Database Migrations

```bash
cd backend
alembic upgrade head          # apply all migrations
alembic revision --autogenerate -m "description"  # generate new migration
```

---

## Seed Demo Data

```bash
cd backend
python scripts/seed.py
```

Creates 60 SYNTHETIC students, 4 semesters of results, all roles, and the demonstration scenario from spec Section 23. **Clearly labeled synthetic — never mix with real data.**

---

## Adding a University-Specific Parser

1. Subclass `BaseParser` in `backend/app/parsers/`
2. Implement `can_parse(file_path)` → `(bool, confidence: float)`
3. Implement `extract(file_path)` → `list[ExtractedRecord]`
4. Register in `backend/app/parsers/plugins.py`
5. Provide golden test PDFs in `backend/tests/golden/`
6. Run golden-file tests: `pytest tests/unit/test_parser_golden.py`

---

## Privacy and Compliance

Designed for **India DPDP Act 2023** by default. Configurable for FERPA/GDPR deployments via `PRIVACY_REGULATION` env var. See `docs/security/privacy-notice.md`.

---

## Responsible AI Statement

AcademicIQ is **decision support only**. It never automatically fails, removes, disciplines, diagnoses, or makes irreversible academic decisions about a student. Every indicator is explainable, versioned, and requires human review. The system openly reports its limits (small samples, missing history, estimated vs. official numbers).

---

## Acceptance Criteria Status

| # | Criterion | Status |
|---|---|---|
| 1 | Parse accuracy ≥ 98% on golden real PDFs | Requires real PDFs — see `tests/golden/` |
| 2 | Student matching: 0 false positives | Enforced: register number only, name = suggested match |
| 3 | Analytics vs. reference: 100% | Run `pytest tests/evaluation/test_h3.py` |
| 4 | Score reproducibility: 100% | Snapshot hash stored per score — `test_h4_reproducibility.py` |
| 5 | Evidence chain completeness: 100% | `GET /evidence/insight/{id}` recursive CTE |
| 6 | AI numeric grounding: 100% on ≥50 insights | Guardrail G1 + `GET /evaluation/run H6` |
| 7 | RBAC matrix: full pass | `pytest tests/rbac/` |
| 8 | Hypothetical labeling: 100% | `HypotheticalBanner` component + `is_hypothetical=True` on all API responses |
| 9 | No-overwrite versioning | `supersedes_upload_id` + `is_latest_attempt` fields |
| 10 | Performance < 2s p95 | Run `pytest tests/performance/test_h8_load.py` |
| 11 | WCAG 2.1 AA | axe scan + manual review required |
| 12 | Audit: 100% of actions logged | `AuditLog` immutable table |
| 13 | All docs present | See `docs/` directory |
| 14 | Demo scenario runs end-to-end | `python scripts/seed.py` |
| 15 | Usability study completed | See `docs/evaluation/h7_usability_study.md` |
