"""Agent 1 — Memory Intake Agent: Validates input, calculates hashes, sandboxes data."""

import uuid
from pathlib import Path
from typing import Optional, Tuple
from echovault.config import config
from echovault.schemas import SourceType, OrchestratorMemoryState, ProcessingStatus
from echovault.services.storage_service import storage_service


class IntakeValidationError(Exception):
    """Raised when an intake payload violates validation rules."""
    pass


class MemoryIntakeAgent:
    name: str = "Memory Intake Agent"

    def process_text_input(
        self,
        content: str,
        narrator: Optional[str] = "Family Member",
        user_title: Optional[str] = None,
        event_date_raw: Optional[str] = None,
    ) -> OrchestratorMemoryState:
        """Validate and stage a written memory for orchestration."""
        cleaned = content.strip()
        if not cleaned:
            raise IntakeValidationError("Memory content cannot be empty.")
        if len(cleaned) > config.max_text_length_chars:
            raise IntakeValidationError(f"Content exceeds maximum allowed characters ({config.max_text_length_chars}).")

        memory_id = str(uuid.uuid4())
        return OrchestratorMemoryState(
            memory_id=memory_id,
            source_type=SourceType.MANUAL_TEXT,
            raw_content=cleaned,
            narrator=narrator or "Family Member",
            processing_status=ProcessingStatus.PENDING,
        )

    def process_audio_input(
        self,
        file_bytes: bytes,
        original_filename: str,
        narrator: Optional[str] = "Family Member",
    ) -> Tuple[OrchestratorMemoryState, Path, str, int]:
        """Validate, hash, and persist audio file before pipeline ingestion."""
        if not file_bytes:
            raise IntakeValidationError("Uploaded audio file is empty.")

        size_mb = len(file_bytes) / (1024 * 1024)
        if size_mb > config.max_audio_size_mb:
            raise IntakeValidationError(
                f"Audio file size ({size_mb:.1f} MB) exceeds limit of {config.max_audio_size_mb} MB."
            )

        ext = Path(original_filename).suffix.lower()
        if ext not in config.allowed_audio_extensions:
            raise IntakeValidationError(
                f"Unsupported audio format '{ext}'. Allowed: {', '.join(config.allowed_audio_extensions)}"
            )

        memory_id = str(uuid.uuid4())
        saved_path, sha256_hash, file_size = storage_service.save_audio(
            file_bytes=file_bytes,
            original_name=original_filename,
            memory_id=memory_id,
        )

        state = OrchestratorMemoryState(
            memory_id=memory_id,
            source_type=SourceType.AUDIO_RECORDING,
            raw_content="",  # Will be populated by Transcription Agent
            raw_audio_path=str(saved_path),
            narrator=narrator or "Family Member",
            processing_status=ProcessingStatus.PENDING,
        )
        return state, saved_path, sha256_hash, file_size


intake_agent = MemoryIntakeAgent()
