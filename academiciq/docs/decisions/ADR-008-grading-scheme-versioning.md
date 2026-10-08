# ADR-008: Grading Scheme — Versioned, Effective-Dated Entity

**Date:** 2026-10-07  
**Status:** Accepted

## Context

Universities update grading regulations (pass marks, grade–mark mappings, GPA formulas) over time. An analytics result computed under the 2018 scheme must remain reproducible even after the 2024 scheme is introduced.

## Decision

- `grading_schemes` table is a versioned, effective-dated entity with `version`, `effective_from`, `effective_to`, `is_active` columns.
- Every analytic record (`student_subject_results`, `academic_attention_scores`, `academic_metrics`) stores `grading_scheme_id` as a foreign key.
- Only one scheme can have `is_active=True` at a time.
- Historical queries specify `grading_scheme_id` explicitly to reproduce past results.
- GPA formula is stored as JSONB (`gpa_formula`); if null, GPA is shown as "Not available from source".
- `repeated_subject_rule` (BEST or LATEST attempt) is a configurable field.

## Consequences

- `GradingSchemeService` in `academics/service.py` manages CRUD.
- `ValidationEngine` loads the active scheme to check grade consistency.
- `AttentionEngine` loads pass mark from the active scheme for F6 and F7 factors.
- `SimulationEngine` stores `grading_scheme_id` on every `WhatIfScenario`.
- No hardcoded pass marks or grade thresholds appear anywhere in application code.
