"""Tests for Gemma service, JSON parsing, recovery, and fallback intelligence."""

import pytest
from unittest.mock import patch, MagicMock
from echovault.services.gemma_service import GemmaService, GemmaServiceError
from echovault.schemas import RetrievedPassage


def test_json_block_extraction():
    """Test extracting JSON from various model response styles."""
    service = GemmaService()

    # Style 1: Clean JSON
    res1 = service._extract_json_block('{"title": "Valid"}')
    assert res1 == {"title": "Valid"}

    # Style 2: Markdown fence with text preamble
    res2 = service._extract_json_block("Here is the requested output:\n```json\n{\"title\": \"Fence\"}\n```\nDone.")
    assert res2 == {"title": "Fence"}

    # Style 3: Embedded brackets with trailing thoughts
    res3 = service._extract_json_block("Output: {\"title\": \"Brackets\"} hope this helps!")
    assert res3 == {"title": "Brackets"}

    # Style 4: Completely invalid
    res4 = service._extract_json_block("Sorry I cannot generate that.")
    assert res4 is None


def test_heuristic_fallback_when_gemma_offline():
    """Verify that when Gemma is unreachable, a safe heuristic record is generated with zero data loss."""
    service = GemmaService(base_url="http://localhost:99999", timeout=1)  # invalid port
    
    story = "In 1948, Uncle Robert built a wooden boat in Boston."
    intel = service.extract_memory_intelligence(story, narrator="Nephew")

    assert intel.title is not None
    assert "Uncle Robert" in intel.summary or "1948" in intel.summary
    assert any(d.iso_year == 1948 for d in intel.dates)
    assert any("offline" in note.lower() for note in intel.uncertainty_notes)


def test_grounded_answer_abstention_when_no_passages():
    """Verify explicit abstention when no evidence exists."""
    service = GemmaService()
    ans = service.answer_question_grounded("What was the secret recipe?", [])
    assert ans.is_abstention is True
    assert ans.answer == "I couldn't find this information in your saved memories."
