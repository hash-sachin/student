# ADR-007: Evidence Graph Storage — Adjacency List in PostgreSQL

**Date:** 2026-10-07  
**Status:** Accepted  
**Alternatives considered:** Neo4j, Apache AGE, pure JSON embedding

## Context

Every analytical insight must be traceable back to its source PDF page. The evidence graph needs to support chain traversal (Insight → Metric → Calculation → Result → Upload/PDF).

## Decision

Store the evidence graph as an **adjacency list** in PostgreSQL:
- `evidence_nodes` table: typed nodes (INSIGHT, METRIC, CALCULATION, STUDENT, SUBJECT, SEMESTER, EXAMINATION, RESULT, SOURCE_UPLOAD)
- `evidence_edges` table: typed directed edges (DERIVED_FROM, COMPUTED_BY, ABOUT, OBSERVED_IN, EXTRACTED_FROM)
- Chain traversal via **recursive CTE** (`WITH RECURSIVE evidence_chain AS (...)`)
- Maximum depth: 10 hops (sufficient for the longest chain)

## Rationale

- PostgreSQL recursive CTEs handle the depth required without a graph database.
- Avoids adding a second database engine (Neo4j) as a required dependency.
- The evidence graph is write-once and read-mostly — PostgreSQL B-tree indexes on `from_node_id` and `to_node_id` are sufficient.
- If graph queries become a bottleneck (>10,000 nodes per entity), Apache AGE (PostgreSQL extension) or Neo4j can be adopted without changing the data model — the adjacency list maps directly.

## Consequences

- `evidence/router.py` uses a raw `text()` SQL with `WITH RECURSIVE` for chain traversal.
- Indexes `ix_evidence_edge_from` and `ix_evidence_edge_to` are defined in the models.
- H5 acceptance criterion (100% of insights resolvable to source PDF) is verifiable via `GET /evidence/insight/{id}` returning `chain_complete: true`.
