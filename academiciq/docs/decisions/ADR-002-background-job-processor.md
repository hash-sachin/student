# ADR-002: Background Job Processor — Celery + Redis

**Date:** 2026-10-07  
**Status:** Accepted  
**Deciders:** Architecture Review  
**Alternatives considered:** RQ, Arq, FastAPI BackgroundTasks only

## Context

PDF processing (extraction, OCR, validation) can take 10–120 seconds for large files. It must not block the HTTP request thread. We need: task queuing, retry on failure, status tracking, and a monitoring UI.

## Decision

Use **Celery 5.x with Redis** as broker and result backend.

- Broker: `redis://redis:6379/1`
- Result backend: `redis://redis:6379/2`
- Flower for job monitoring UI at port 5555
- `app/celery_app.py` defines the Celery application
- `app/results/pipeline.py` contains the pipeline logic (also usable as FastAPI BackgroundTask for dev)

## Rationale

- Celery is the most widely adopted Python task queue with extensive documentation.
- Redis is already required for session management and caching; adding a second service is low cost.
- Flower provides observability out of the box.
- RQ is simpler but lacks retry policies and canvas workflows needed for multi-stage pipelines.
- Arq is async-native but has less ecosystem support and no built-in UI.

## Consequences

- Redis is a required service dependency (see `docker-compose.yml`).
- The pipeline logic is decoupled from the HTTP layer — it can run in Celery worker OR as a FastAPI BackgroundTask for local development.
- A `celery_worker` service is defined in Docker Compose.
- Task state transitions (`QUEUED → PROCESSING → VALIDATION → READY_FOR_REVIEW → COMMITTED | FAILED`) are stored in `result_uploads.processing_status`.

## Review trigger

Revisit if Redis availability becomes a constraint in the target deployment environment.
