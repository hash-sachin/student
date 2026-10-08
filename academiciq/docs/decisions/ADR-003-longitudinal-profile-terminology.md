# ADR-003: Terminology — Longitudinal Academic Profile vs. Academic Digital Twin

**Date:** 2026-10-07  
**Status:** Accepted

## Context

The phrase "Academic Digital Twin" appeared in early project scoping. "Digital twin" has a specific meaning in engineering (a real-time synchronized model of a physical system). Applying it to a student academic record without justification risks misleading users and reviewers.

## Decision

- **Primary term:** "Longitudinal Academic Profile" — used in all code, APIs, database schemas, UI labels, and research outputs.
- **Secondary alias:** "Academic Digital Twin" — permitted as a secondary/branding label only in the frontend (`/digital-twin/student/{id}` API alias, profile note text) and only with an accompanying explanatory note.
- The explanatory note reads: *"This is a Longitudinal Academic Profile — a structured representation of a student's academic history over time. 'Academic Digital Twin' is a secondary alias."*
- Research papers must not claim equivalence to physical/engineering digital twins without a literature-supported justification.

## Rationale

Clarity and intellectual honesty. The literature review (`docs/literature-review.md`) did not find sufficient prior use of "academic digital twin" to justify the term as established. Longitudinal Academic Profile accurately describes what the system does.

## Consequences

- API route `/profile/student/{id}` is canonical; `/digital-twin/student/{id}` is an alias.
- `ProfileService.get_longitudinal_profile()` is the method name throughout the codebase.
- Frontend renders a profile note banner on every profile page.
