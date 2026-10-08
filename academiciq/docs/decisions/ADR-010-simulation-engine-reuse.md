# ADR-010: What-If Simulation Reuses Production L1 Engines

**Date:** 2026-10-07  
**Status:** Accepted

## Context

A what-if simulator could be implemented with a separate simplified calculation path. This creates a maintenance problem: divergence between what the simulator shows and what the real system computes.

## Decision

The What-If Simulation Engine (`simulation/engine.py`) **reuses the exact same deterministic calculation logic** as the production analytics engine. There is no separate simulation logic:

- Grade computation reuses `_compute_grade()` from the grading scheme.
- Pass/fail determination uses the same `pass_mark_overall` from the active grading scheme.
- Average calculation uses the same numpy mean.
- The engine calls `GradingSchemeService` for the same scheme version.

The only difference: simulation outputs are written to `what_if_scenarios` (never to `student_subject_results`) and every output carries `is_hypothetical=True` enforced at the DB column level (default=True, non-nullable).

## Consequences

- A test (`tests/unit/test_simulation.py`) verifies that a hypothetical scenario recomputing unchanged marks produces identical output to the real analytics engine.
- `WhatIfScenario.is_hypothetical` is a non-nullable boolean defaulting to True — application code cannot accidentally set it to False.
- The `HypotheticalBanner` component is rendered on every simulation output in the frontend; its presence is tested in `src/test/HypotheticalBanner.test.tsx`.
- Acceptance criterion #8 (hypothetical labeling in 100% of UI/export/API outputs) is enforced by the router (`simulation/router.py` always adds `hypothetical_banner` key) and tested.
