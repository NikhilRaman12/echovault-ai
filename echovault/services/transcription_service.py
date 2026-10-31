"""Local audio transcription service with faster-whisper and graceful fallback."""

import logging
from pathlib import Path
from typing import Tuple, Dict, Any, List

logger = logging.getLogger(__name__)


class TranscriptionService:
    def __init__(self, model_size: str = "tiny"):
        self.model_size = model_size
        self._whisper_model = None
        self._is_available = self._check_availability()

    def _check_availability(self) -> bool:
        """Check if faster-whisper can be imported and executed locally."""
        try:
            import faster_whisper  # noqa
            return True
        except ImportError:
            return False

    @property
    def is_available(self) -> bool:
        return self._is_available

    def transcribe(self, audio_path: Path) -> Tuple[str, List[Dict[str, Any]], str]:
        """
        Transcribe local audio file using faster-whisper.
        Returns: (transcript_text, segments_with_timestamps, model_used)
        """
        if not self._is_available:
            # Graceful degraded fallback: inform user and allow manual transcript entry
            return (
                "[Local faster-whisper is not installed or FFmpeg is missing. You can listen to the audio recording in the vault and edit or provide the transcript text manually.]",
                [],
                "offline-placeholder",
            )

        try:
            from faster_whisper import WhisperModel
            if self._whisper_model is None:
                # Load on CPU with int8 quantization to conserve memory
                self._whisper_model = WhisperModel(self.model_size, device="cpu", compute_type="int8")

            segments, info = self._whisper_model.transcribe(str(audio_path), beam_size=1)
            
            segment_list = []
            full_text_parts = []
            for s in segments:
                segment_list.append({
                    "start": round(s.start, 2),
                    "end": round(s.end, 2),
                    "text": s.text.strip(),
                })
                full_text_parts.append(s.text.strip())

            full_transcript = " ".join(full_text_parts)
            return full_transcript, segment_list, f"faster-whisper-{self.model_size}"
        except Exception as e:
            logger.warning(f"Audio transcription failed: {e}")
            return (
                f"[Audio transcription could not be completed automatically: {str(e)}. Please edit transcript manually.]",
                [],
                "error-fallback",
            )


transcription_service = TranscriptionService()
