"""Tests for Intake Agent, duplicate rejection, and file sandboxing."""

import pytest
from echovault.agents.intake_agent import intake_agent, IntakeValidationError
from echovault.services.storage_service import storage_service, StorageSecurityError
from pathlib import Path


def test_intake_empty_text_rejection():
    """Verify empty text input raises validation error."""
    with pytest.raises(IntakeValidationError):
        intake_agent.process_text_input("")


def test_intake_valid_text():
    """Verify valid text generates a compliant state."""
    state = intake_agent.process_text_input(
        content="Synthetic story for testing intake pipeline.",
        narrator="Synthetic Narrator",
    )
    assert state.memory_id is not None
    assert state.raw_content == "Synthetic story for testing intake pipeline."
    assert state.narrator == "Synthetic Narrator"


def test_intake_audio_unsupported_extension():
    """Verify unsupported extensions are rejected."""
    with pytest.raises(IntakeValidationError):
        intake_agent.process_audio_input(
            file_bytes=b"synthetic bytes",
            original_filename="malicious.exe",
        )


def test_storage_sandbox_protection():
    """Verify path traversal outside data directory is prevented."""
    outside_path = Path("C:/Windows/System32/calc.exe")
    with pytest.raises(StorageSecurityError):
        storage_service.verify_sandbox(outside_path)
