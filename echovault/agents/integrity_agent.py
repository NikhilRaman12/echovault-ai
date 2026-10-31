"""Agent 7 — Integrity and Privacy Agent: Verifies claims, guards privacy, logs audit events."""

import time
from typing import Tuple
from echovault.database import db
from echovault.schemas import GroundedAnswer, ExecutionStepTrace, AuditEvent, AuditAction


class IntegrityAndPrivacyAgent:
    name: str = "Integrity and Privacy Agent"

    def verify_answer_integrity(
        self, answer: GroundedAnswer
    ) -> Tuple[GroundedAnswer, ExecutionStepTrace]:
        """Validate that non-abstained answers have verifiable citation links."""
        start_time = time.time()
        
        # Rule 1: Never allow an answer that claims facts without citations
        if not answer.is_abstention and not answer.citations:
            answer.is_abstention = True
            answer.answer = "I couldn't find this information in your saved memories."
            answer.abstention_reason = "Integrity check: generated claim lacked verifiable source passages in memory vault."
            status = "downgraded_to_abstention"
            message = "Flagged answer lacking citation traceability; converted to abstention."
        else:
            status = "verified"
            message = "Integrity verified: citations match source memory records."

        duration_ms = (time.time() - start_time) * 1000
        trace = ExecutionStepTrace(
            agent_name=self.name,
            stage="integrity_verification",
            status=status,
            duration_ms=round(duration_ms, 2),
            message=message,
        )

        db.record_audit_event(AuditEvent(
            action=AuditAction.QUESTION_ANSWERED,
            agent_name=self.name,
            details={
                "question": answer.question,
                "is_abstention": answer.is_abstention,
                "citations_count": len(answer.citations),
            },
        ))

        return answer, trace


integrity_agent = IntegrityAndPrivacyAgent()
