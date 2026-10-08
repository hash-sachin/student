# ADR-006: LLM Provider — Local Ollama (default), External API (optional)

**Date:** 2026-10-07  
**Status:** Accepted  
**Alternatives considered:** OpenAI GPT-4o, Anthropic Claude, Azure OpenAI, Ollama local

## Context

AI Insights (Layer 3) require an LLM. The system must comply with DPDP Act 2023 — student names and register numbers must not leave the institution's infrastructure.

## Decision

- **Default:** Local Ollama instance (`LLM_PROVIDER=local`, `LLM_BASE_URL=http://localhost:11434`).
- **Optional:** OpenAI API (`LLM_PROVIDER=openai`) — only permitted when the evidence payload is fully pseudonymized (no names, no register numbers; entity token only).
- Anthropic Claude is supported in `ai/service.py` as a future option.

## Privacy contract

Before any data reaches an external LLM:
1. Student names are removed.
2. Register numbers are removed.
3. Entity is replaced with a pseudonymized token (`ENTITY_<first-8-chars-of-UUID>`).
4. Only aggregated metric values are included.

The guardrail G2 (entity verifier) rejects any AI output that contains register number patterns, enforcing that the LLM did not receive and repeat identifying information.

## Consequences

- `settings.LLM_PROVIDER` controls routing in `ai/service.py`.
- `settings.OPENAI_API_KEY` is optional; only read if `LLM_PROVIDER=openai`.
- Ollama is defined as an optional Docker Compose service (`--profile ai`).
- All data flows are documented in `docs/security/ai-data-flow.md`.
