# ADR-009: Student Matching — Register Number as Primary Key, Name as Suggested Match Only

**Date:** 2026-10-07  
**Status:** Accepted (Non-negotiable — safety constraint)

## Context

Incorrect student matching (e.g., assigning marks to the wrong student) is a high-severity data integrity failure with real academic consequences.

## Decision

1. **Register number is the only authoritative match key.** Every extraction validates `raw_register_number` against `students.register_number` with exact string match.
2. **Name similarity is explicitly forbidden as an automatic match.** `StudentService.find_by_name_similarity()` returns suggested matches ONLY — flagged with a human-confirmation requirement. It never triggers an automatic assignment.
3. If a register number is not found, the extracted record is assigned `ValidationRecordStatus.UNMATCHED` — it is stored, surfaced in the validation preview, and requires admin action (map, skip-with-reason, or reject).
4. University register number (`university_register_number`) is a secondary lookup field — also exact match only.

## Rationale

Name-based fuzzy matching has failed in production academic systems resulting in mark assignment errors. H2 acceptance criterion requires 0 false-positive matches.

## Consequences

- `ValidationEngine._validate_one()` performs only exact register number lookup.
- The staging record stores both `raw_register_number` and the resolved `student_id` (null if unmatched).
- Admin UI shows unmatched records prominently with a suggested-name search that is visually marked "SUGGESTED — requires confirmation".
- Any match via name must be manually confirmed by admin before `student_id` is written.
