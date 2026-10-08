# ADR-001: Three Strictly Separated Intelligence Layers

**Date:** 2026-10-07  
**Status:** Accepted  
**Deciders:** Architecture Review

## Context

AcademicIQ needs to combine rule-based analytics, optional ML prediction, and generative AI explanation. Without strict separation, AI outputs could claim authority they don't have (e.g., calculating official GPA), and ML outputs could contaminate ground truth labels (circular validation).

## Decision

Implement three layers with hard contracts between them:

- **Layer 1 — Deterministic Analytics:** All statistics, attendance counts, comparisons, and attention scores. Reproducible. Labels: CALCULATED or ESTIMATED.
- **Layer 2 — Machine Learning (gated):** Optional. Activates only when data thresholds from Section 10 of the spec are met. Uses independent ground truth — never the rule-engine's own output. Labels: ESTIMATED.
- **Layer 3 — Generative AI:** Receives only verified metrics payload (pseudonymized). Never calculates authoritative numbers. Outputs verified by 5 programmatic guardrails before storage. Labels: ESTIMATED.

## Consequences

- No single module spans layers. `analytics/engine.py`, `intelligence/attention_engine.py`, `simulation/engine.py` are all Layer 1 only.
- The AI service (`ai/service.py`) receives a pre-built evidence payload — it never queries the database directly.
- ML is a separate optional module (`ml/`) gated by `MLService.check_activation_thresholds()`.
- Metric labels are enforced at the DB column level (`metric_label` Enum) and in every API response.
