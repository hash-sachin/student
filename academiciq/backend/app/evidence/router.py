"""Evidence graph API router."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.database.session import get_db
from app.database.models import EvidenceEdge, EvidenceNode

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.get("/{node_id}")
async def get_evidence_node(
    node_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    r = await db.execute(select(EvidenceNode).where(EvidenceNode.id == node_id))
    node = r.scalar_one_or_none()
    if not node:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("EvidenceNode", node_id)
    return {
        "id": str(node.id),
        "node_type": node.node_type.value,
        "entity_id": str(node.entity_id) if node.entity_id else None,
        "label": node.label,
        "data": node.data,
    }


@router.get("/insight/{insight_id}")
async def get_insight_evidence_chain(
    insight_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Resolve the full evidence chain for an AI insight.
    Chain: Insight → Metric → Calculation → Result records → Source PDF
    Uses recursive CTE for chain traversal.
    """
    # Recursive CTE to traverse evidence graph
    cte_sql = text("""
        WITH RECURSIVE evidence_chain AS (
            SELECT id, node_type, entity_id, label, data, 0 AS depth
            FROM evidence_nodes
            WHERE entity_id = :insight_id
            UNION ALL
            SELECT n.id, n.node_type, n.entity_id, n.label, n.data, ec.depth + 1
            FROM evidence_nodes n
            JOIN evidence_edges e ON e.to_node_id = n.id
            JOIN evidence_chain ec ON ec.id = e.from_node_id
            WHERE ec.depth < 10
        )
        SELECT * FROM evidence_chain ORDER BY depth
    """)

    r = await db.execute(cte_sql, {"insight_id": insight_id})
    rows = r.fetchall()

    chain = [
        {
            "id": str(row.id),
            "node_type": row.node_type,
            "entity_id": str(row.entity_id) if row.entity_id else None,
            "label": row.label,
            "depth": row.depth,
        }
        for row in rows
    ]

    return {
        "insight_id": str(insight_id),
        "chain": chain,
        "chain_complete": len(chain) > 0,
    }
