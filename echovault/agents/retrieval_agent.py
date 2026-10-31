"""Agent 5 — Memory Retrieval Agent: Full-text search and transparent snippet ranking."""

import time
from typing import List, Tuple
from echovault.database import db
from echovault.schemas import RetrievedPassage, ExecutionStepTrace, AuditEvent, AuditAction
from echovault.services.retrieval_service import retrieval_service


class MemoryRetrievalAgent:
    name: str = "Memory Retrieval Agent"

    def search(self, query: str, limit: int = 5) -> Tuple[List[RetrievedPassage], ExecutionStepTrace]:
        """Search archived memories with FTS5 and BM25 ranking."""
        start_time = time.time()
        passages = retrieval_service.retrieve_passages(query, limit=limit)
        duration_ms = (time.time() - start_time) * 1000

        trace = ExecutionStepTrace(
            agent_name=self.name,
            stage="retrieval_search",
            status="success",
            duration_ms=round(duration_ms, 2),
            message=f"Retrieved {len(passages)} relevant memory passages via FTS5 for query: '{query}'",
        )

        db.record_audit_event(AuditEvent(
            action=AuditAction.SEARCH_RETRIEVED,
            agent_name=self.name,
            details={"query": query, "results_count": len(passages)},
        ))

        return passages, trace


retrieval_agent = MemoryRetrievalAgent()
