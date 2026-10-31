"""Tests for memory export (JSON/Markdown) and backup restoration."""

import gc
import json
import pytest
from echovault.database import Database
from echovault.services.export_service import ExportService
from echovault.schemas import MemoryRecord, SourceType
import tempfile
from pathlib import Path


@pytest.fixture
def isolated_env():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        db_path = Path(tmpdir) / "export_test.db"
        test_db = Database(db_path=db_path)
        service = ExportService(database=test_db)
        yield test_db, service
        gc.collect()


def test_export_and_restore_cycle(isolated_env):
    """Test round-trip export to JSON and restoration."""
    db, exp = isolated_env

    # 1. Insert original memory
    rec = MemoryRecord(
        id="mem-export-01",
        title="Family Clock Story",
        content="Grandfather's wall clock was brought from Munich in 1920.",
        content_hash="hash-clock-01",
        source_type=SourceType.MANUAL_TEXT,
    )
    db.insert_memory_record(rec)

    # 2. Export to JSON
    json_export = exp.export_archive_to_json()
    assert "Family Clock Story" in json_export

    # 3. Export to Markdown
    md_export = exp.export_archive_to_markdown()
    assert "# EchoVault AI — Family Memory Archive" in md_export
    assert "Family Clock Story" in md_export

    # 4. Create second DB and restore
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir2:
        db2 = Database(db_path=Path(tmpdir2) / "restore_target.db")
        exp2 = ExportService(database=db2)
        
        imported, skipped = exp2.restore_archive_from_json(json_export)
        assert imported == 1
        assert skipped == 0

        restored_mem = db2.get_memory("mem-export-01")
        assert restored_mem is not None
        assert restored_mem.title == "Family Clock Story"

        # Try re-importing same JSON -> should skip duplicate
        imported2, skipped2 = exp2.restore_archive_from_json(json_export)
        assert imported2 == 0
        assert skipped2 == 1
        gc.collect()
