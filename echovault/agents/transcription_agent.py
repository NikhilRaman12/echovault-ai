"""Agent 2 — Transcription Agent: Local Whisper audio processing with manual editing support."""

import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from echovault.schemas import OrchestratorMemoryState, ExecutionStepTrace, SourceType
from echovault.services.transcription_service import transcription_service


class TranscriptionAgent:
    name: str = "Transcription Agent"

    def process(
        self, state: OrchestratorMemoryState, manual_transcript_override: Optional[str] = None
    ) -> OrchestratorMemoryState:
        """Transcribe audio or register manual transcription pass."""
        if state.source_type != SourceType.AUDIO_RECORDING:
            # Skip for text inputs
            return state

        start_time = time.time()
        
        # If user supplied a manual correction
        if manual_transcript_override and manual_transcript_override.strip():
            state.transcript_text = manual_transcript_override.strip()
            state.raw_content = manual_transcript_override.strip()
            duration_ms = (time.time() - start_time) * 1000
            state.traces.append(ExecutionStepTrace(
                agent_name=self.name,
                stage="manual_override",
                status="success",
                duration_ms=round(duration_ms, 2),
                message="User applied manual transcript edit or review.",
            ))
            return state

        if not state.raw_audio_path:
            state.errors.append("Audio recording path missing from intake state.")
            return state

        audio_file = Path(state.raw_audio_path)
        transcript_text, segments, model_used = transcription_service.transcribe(audio_file)
        
        state.transcript_text = transcript_text
        state.raw_content = transcript_text
        
        duration_ms = (time.time() - start_time) * 1000
        state.traces.append(ExecutionStepTrace(
            agent_name=self.name,
            stage="transcription",
            status="completed" if transcription_service.is_available else "offline_fallback",
            duration_ms=round(duration_ms, 2),
            message=f"Transcribed using {model_used} ({len(segments)} segments captured).",
        ))
        return state


transcription_agent = TranscriptionAgent()
