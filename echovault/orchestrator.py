"""Deterministic multi-agent orchestrator managing shared typed state and execution traces."""

import logging
from typing import Optional, List, Tuple
from echovault.schemas import (
    OrchestratorMemoryState,
    MemorySource,
    SourceType,
    ProcessingStatus,
    GroundedAnswer,
    RetrievedPassage,
    ExecutionStepTrace,
)
from echovault.agents.intake_agent import intake_agent
from echovault.agents.transcription_agent import transcription_agent
from echovault.agents.memory_intelligence_agent import memory_intelligence_agent
from echovault.agents.archivist_agent import archivist_agent
from echovault.agents.retrieval_agent import retrieval_agent
from echovault.agents.remembrance_agent import remembrance_agent
from echovault.agents.integrity_agent import integrity_agent

logger = logging.getLogger(__name__)


class MemoryOrchestrator:
    def __init__(self):
        self.intake = intake_agent
        self.transcription = transcription_agent
        self.intelligence = memory_intelligence_agent
        self.archivist = archivist_agent
        self.retrieval = retrieval_agent
        self.remembrance = remembrance_agent
        self.integrity = integrity_agent

    def process_text_memory(
        self,
        content: str,
        narrator: str = "Family Member",
        user_title: Optional[str] = None,
        event_date_raw: Optional[str] = None,
    ) -> OrchestratorMemoryState:
        """Execute full deterministic pipeline for a written memory."""
        # Stage 1: Intake
        state = self.intake.process_text_input(
            content=content,
            narrator=narrator,
            user_title=user_title,
            event_date_raw=event_date_raw,
        )

        # Stage 2: Memory Intelligence (Gemma extraction)
        state = self.intelligence.process(state)

        # Stage 3: Archival
        source_record = MemorySource(
            id=state.memory_id,
            memory_id=state.memory_id,
            source_type=SourceType.MANUAL_TEXT,
            content_sha256=state.archived_record.content_hash if state.archived_record else "hash_pending",
            file_size_bytes=len(content.encode("utf-8")),
        )
        state = self.archivist.process(state, source_record=source_record)

        return state

    def process_audio_memory(
        self,
        audio_bytes: bytes,
        filename: str,
        narrator: str = "Family Member",
        manual_transcript_override: Optional[str] = None,
    ) -> OrchestratorMemoryState:
        """Execute full pipeline for an audio memory recording."""
        # Stage 1: Intake & Sandbox Storage
        state, saved_path, sha256_hash, file_size = self.intake.process_audio_input(
            file_bytes=audio_bytes,
            original_filename=filename,
            narrator=narrator,
        )

        # Stage 2: Audio Transcription
        state = self.transcription.process(state, manual_transcript_override=manual_transcript_override)

        # If transcription produced valid text, run intelligence extraction
        if state.raw_content and state.raw_content.strip():
            state = self.intelligence.process(state)

        # Stage 3: Archival
        source_record = MemorySource(
            id=state.memory_id,
            memory_id=state.memory_id,
            source_type=SourceType.AUDIO_RECORDING,
            original_filename=filename,
            file_path=str(saved_path),
            file_size_bytes=file_size,
            content_sha256=sha256_hash,
        )
        state = self.archivist.process(state, source_record=source_record)

        return state

    def answer_question(self, question: str, max_evidence_items: int = 5) -> Tuple[GroundedAnswer, List[ExecutionStepTrace]]:
        """
        Orchestrate grounded question answering:
        Retrieval Agent -> Remembrance Agent -> Integrity Agent
        """
        traces: List[ExecutionStepTrace] = []

        # Step 1: Retrieval
        passages, ret_trace = self.retrieval.search(question, limit=max_evidence_items)
        traces.append(ret_trace)

        # Step 2: Remembrance Synthesis
        candidate_answer, rem_trace = self.remembrance.answer_inquiry(question, passages)
        traces.append(rem_trace)

        # Step 3: Integrity & Privacy Verification
        verified_answer, int_trace = self.integrity.verify_answer_integrity(candidate_answer)
        traces.append(int_trace)

        return verified_answer, traces


orchestrator = MemoryOrchestrator()
