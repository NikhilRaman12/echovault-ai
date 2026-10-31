"""Tests for Retrieval, Remembrance, and Integrity Agents."""

import pytest
from echovault.schemas import RetrievedPassage, GroundedAnswer
from echovault.agents.remembrance_agent import remembrance_agent
from echovault.agents.integrity_agent import integrity_agent


def test_integrity_agent_abstention_on_empty_citations():
    """Verify integrity agent downgrades claims to abstention if citations are missing."""
    unverified_claim = GroundedAnswer(
        question="Where did grandma live?",
        answer="She lived in Paris.",  # Claim without supporting citation
        citations=[],
        supporting_memory_titles=[],
        is_abstention=False,
    )

    verified, trace = integrity_agent.verify_answer_integrity(unverified_claim)
    assert verified.is_abstention is True
    assert verified.answer == "I couldn't find this information in your saved memories."
    assert trace.status == "downgraded_to_abstention"


def test_integrity_agent_passes_verified_citations():
    """Verify integrity agent allows answers backed by real evidence."""
    passage = RetrievedPassage(
        memory_id="mem-1",
        title="Grandma in Savannah",
        passage="Grandmother lived in Savannah in 1944.",
        relevance_score=2.5,
    )
    grounded = GroundedAnswer(
        question="Where did grandma live?",
        answer="According to the memory 'Grandma in Savannah', she lived in Savannah.",
        citations=[passage],
        supporting_memory_titles=["Grandma in Savannah"],
        is_abstention=False,
    )

    verified, trace = integrity_agent.verify_answer_integrity(grounded)
    assert verified.is_abstention is False
    assert trace.status == "verified"
    assert len(verified.citations) == 1
