"""End-to-end orchestrator pipeline tests."""

import uuid
import pytest
from echovault.orchestrator import MemoryOrchestrator


def test_orchestrator_text_pipeline():
    """Test full workflow from intake through archival and trace recording."""
    orc = MemoryOrchestrator()
    unique_run_id = str(uuid.uuid4())[:8]
    
    state = orc.process_text_memory(
        content=f"In 1960, my father purchased our first family automobile, a blue Chevrolet station wagon. (Batch {unique_run_id})",
        narrator="Son David",
        user_title=f"The Blue Chevrolet {unique_run_id}",
    )

    assert state.processing_status.value == "completed"
    assert state.archived_record is not None
    assert state.archived_record.title is not None
    assert len(state.traces) >= 2  # Intake, Intelligence, Archival
    assert any("safely archived" in t.message.lower() for t in state.traces)


def test_orchestrator_qa_abstention():
    """Test inquiry on non-existent topic returns honest abstention."""
    orc = MemoryOrchestrator()
    
    answer, traces = orc.answer_question("What was our pet parrot named in Antarctica?")
    assert answer.is_abstention is True
    assert answer.answer == "I couldn't find this information in your saved memories."
    assert len(traces) == 3  # Retrieval, Remembrance, Integrity
