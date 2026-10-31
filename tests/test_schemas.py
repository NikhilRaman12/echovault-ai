"""Automated tests for Pydantic data models and validation."""

import pytest
from pydantic import ValidationError
from echovault.schemas import (
    MemoryIntelligence,
    ExtractedPerson,
    ExtractedPlace,
    ExtractedDate,
    ExtractedQuote,
    MemoryRecord,
    ProcessingStatus,
    SourceType,
)


def test_memory_intelligence_schema():
    """Verify structured memory intelligence validates required fields."""
    intel = MemoryIntelligence(
        title="Synthetic Childhood Memory",
        summary="A brief synthetic recollection.",
        people=[ExtractedPerson(name="Sarah", relationship="Aunt", context="visiting on Sundays")],
        places=[ExtractedPlace(name="Savannah", location_type="city")],
        dates=[ExtractedDate(raw_date="Summer of 1964", iso_year=1964, is_approximate=False)],
        quotes=[ExtractedQuote(quote_text="Always remember where you came from.", speaker="Sarah")],
        themes=["family", "tradition"],
        topics=["Sunday dinners"],
        explicit_facts=["Dinner was held at 2 PM."],
        uncertainty_notes=[],
    )
    assert intel.title == "Synthetic Childhood Memory"
    assert intel.people[0].name == "Sarah"
    assert intel.dates[0].iso_year == 1964


def test_memory_record_defaults():
    """Test default values on memory record."""
    rec = MemoryRecord(
        id="test-123",
        title="Title",
        content="Some content",
        content_hash="hash123",
    )
    assert rec.processing_status == ProcessingStatus.PENDING
    assert rec.source_type == SourceType.MANUAL_TEXT
    assert rec.narrator == "Family Member"
