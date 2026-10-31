"""Agent 6 — Remembrance Intelligence Agent: Evidence-grounded Q&A with strict abstention."""

import time
from typing import List, Tuple
from echovault.schemas import GroundedAnswer, RetrievedPassage, ExecutionStepTrace
from echovault.services.gemma_service import gemma_service


class RemembranceIntelligenceAgent:
    name: str = "Remembrance Intelligence Agent"

    def answer_inquiry(
        self, question: str, retrieved_passages: List[RetrievedPassage]
    ) -> Tuple[GroundedAnswer, ExecutionStepTrace]:
        """Synthesize answer strictly from retrieved evidence or abstain when absent."""
        start_time = time.time()
        
        answer = gemma_service.answer_question_grounded(question, retrieved_passages)
        duration_ms = (time.time() - start_time) * 1000

        trace = ExecutionStepTrace(
            agent_name=self.name,
            stage="grounded_synthesis",
            status="abstained" if answer.is_abstention else "answered",
            duration_ms=round(duration_ms, 2),
            message=(
                "Abstained from fabricating information (no matching evidence)."
                if answer.is_abstention
                else f"Answer generated from {len(answer.citations)} supporting memory citations."
            ),
        )
        return answer, trace


remembrance_agent = RemembranceIntelligenceAgent()
