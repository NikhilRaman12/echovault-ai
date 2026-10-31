"""Automated tests for SQLite database operations, FTS5 full-text search, and migrations."""

import gc
import os
import tempfile
from pathlib import Path
import pytest
from echovault.database import Database
from echovault.schemas import (
    MemoryRecord,
    ProcessingStatus,
    SourceType,
    ExtractedPerson,
    ExtractedPlace,
    ExtractedQuote,
    AuditEvent,
    AuditAction,
)


@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        db_path = Path(tmpdir) / "test_echovault.db"
        test_db = Database(db_path=db_path)
        yield test_db
        gc.collect()


def test_db_initialization(temp_db):
    """Test that all tables and FTS5 virtual tables are correctly initialized."""
    with temp_db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cursor.fetchall()]
        assert "memories" in tables
        assert "memory_sources" in tables
        assert "memory_entities" in tables
        assert "memories_fts" in tables
        assert "memory_audit_events" in tables


def test_insert_and_get_memory(temp_db):
    """Test inserting a memory with entities and retrieving it."""
    record = MemoryRecord(
        id="mem-synthetic-001",
        title="Synthetic Grandfather Farm Memory",
        content="Grandfather Arthur lived on a farm in Kansas during the 1930s dust bowl.",
        summary="Synthetic story about farming in Kansas.",
        narrator="Synthetic Arthur",
        event_date_raw="1935",
        event_date_iso="1935",
        content_hash="hash-synthetic-001",
        source_type=SourceType.MANUAL_TEXT,
        processing_status=ProcessingStatus.COMPLETED,
        people=[ExtractedPerson(name="Arthur", relationship="Grandfather")],
        places=[ExtractedPlace(name="Kansas", location_type="state")],
        quotes=[ExtractedQuote(quote_text="The dust was everywhere.", speaker="Arthur")],
    )

    mem_id = temp_db.insert_memory_record(
        record=record,
        entities=[
            {"type": "person", "name": "Arthur", "secondary_value": "Grandfather"},
            {"type": "place", "name": "Kansas", "secondary_value": "state"},
        ],
        themes=["farming", "dust bowl"],
        quotes=record.quotes,
    )
    assert mem_id == "mem-synthetic-001"

    retrieved = temp_db.get_memory("mem-synthetic-001")
    assert retrieved is not None
    assert retrieved.title == "Synthetic Grandfather Farm Memory"
    assert len(retrieved.people) == 1
    assert retrieved.people[0].name == "Arthur"
    assert len(retrieved.places) == 1
    assert retrieved.places[0].name == "Kansas"
    assert len(retrieved.quotes) == 1


def test_fts5_search(temp_db):
    """Test SQLite FTS5 search indexing and ranking."""
    record = MemoryRecord(
        id="mem-fts-002",
        title="The Old Sailing Ship",
        content="We sailed across the Atlantic Ocean on the vessel called Aurora in 1952.",
        summary="A voyage across the Atlantic.",
        narrator="Great Uncle Charles",
        content_hash="hash-aurora-002",
        source_type=SourceType.MANUAL_TEXT,
    )
    temp_db.insert_memory_record(record=record)

    # Search for Atlantic
    results = temp_db.search_memories("Atlantic")
    assert len(results) > 0
    assert results[0].memory_id == "mem-fts-002"
    assert "Atlantic" in results[0].passage or "Aurora" in results[0].passage

    # Search for non-existent word
    empty_results = temp_db.search_memories("SubmarineXYZNonExistent")
    assert len(empty_results) == 0


def test_duplicate_detection(temp_db):
    """Test content hash duplicate check."""
    record = MemoryRecord(
        id="mem-dup-003",
        title="Duplicate Story",
        content="Identical content for duplicate check.",
        content_hash="dup-hash-12345",
        source_type=SourceType.MANUAL_TEXT,
    )
    temp_db.insert_memory_record(record=record)

    dup_id = temp_db.find_duplicate_by_hash("dup-hash-12345")
    assert dup_id == "mem-dup-003"

    no_dup = temp_db.find_duplicate_by_hash("unique-hash-99999")
    assert no_dup is None


def test_delete_memory(temp_db):
    """Test safe deletion and FTS cleanup."""
    record = MemoryRecord(
        id="mem-del-004",
        title="Memory To Delete",
        content="This memory will be purged completely.",
        content_hash="del-hash-004",
        source_type=SourceType.MANUAL_TEXT,
    )
    temp_db.insert_memory_record(record=record)
    assert temp_db.get_memory("mem-del-004") is not None

    deleted = temp_db.delete_memory("mem-del-004")
    assert deleted is True
    assert temp_db.get_memory("mem-del-004") is None

    # Verify removed from FTS5
    results = temp_db.search_memories("purged")
    assert len(results) == 0
