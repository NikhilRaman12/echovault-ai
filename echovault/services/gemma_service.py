"""Service interface for local Gemma inference via Ollama."""

import json
import logging
import re
from typing import Optional, Dict, Any, Tuple
import requests

from echovault.config import config
from echovault.schemas import MemoryIntelligence, GroundedAnswer, RetrievedPassage

logger = logging.getLogger(__name__)


class GemmaServiceError(Exception):
    """Raised when Gemma / Ollama fails or times out."""
    pass


class GemmaService:
    def __init__(
        self,
        base_url: str = config.ollama_base_url,
        model: str = config.gemma_model,
        timeout: int = config.ollama_timeout_seconds,
        max_retries: int = config.ollama_max_retries,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

    def check_health(self) -> Tuple[bool, str, list]:
        """Check if Ollama is reachable and query available models."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name") for m in data.get("models", [])]
                model_found = self.model in models or any(m.startswith(self.model.split(":")[0]) for m in models)
                status_msg = f"Connected. Active target: {self.model} ({'available' if model_found else 'not downloaded'})"
                return True, status_msg, models
            return False, f"Ollama returned HTTP {resp.status_code}", []
        except Exception as e:
            return False, f"Cannot connect to Ollama at {self.base_url}: {str(e)}", []

    def _extract_json_block(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract and parse JSON from model output, handling markdown fences and stray text."""
        if not text:
            return None
        
        # 1. Direct parse attempt
        try:
            return json.loads(text.strip())
        except Exception:
            pass

        # 2. Markdown ```json ... ``` regex
        json_matches = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        for m in json_matches:
            try:
                return json.loads(m.strip())
            except Exception:
                continue

        # 3. First '{' to last '}' bracket slice
        start_idx = text.find("{")
        end_idx = text.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            candidate = text[start_idx : end_idx + 1]
            try:
                return json.loads(candidate)
            except Exception:
                pass

        return None

    def call_ollama(self, prompt: str, system_prompt: Optional[str] = None, format_json: bool = True) -> str:
        """Call Ollama /api/generate with retry and error propagation."""
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,  # Low temperature to prevent hallucination
                "num_ctx": 2048,
            }
        }
        if system_prompt:
            payload["system"] = system_prompt
        if format_json:
            payload["format"] = "json"

        last_error = ""
        for attempt in range(self.max_retries + 1):
            try:
                resp = requests.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=self.timeout,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("response", "").strip()
                else:
                    last_error = f"HTTP {resp.status_code}: {resp.text}"
            except requests.exceptions.Timeout:
                last_error = f"Ollama request timed out after {self.timeout}s"
            except requests.exceptions.ConnectionError:
                last_error = f"Could not connect to Ollama service at {self.base_url}"
            except Exception as e:
                last_error = str(e)

        raise GemmaServiceError(f"Gemma model '{self.model}' generation failed: {last_error}")

    def extract_memory_intelligence(self, raw_story: str, narrator: str = "Family Member") -> MemoryIntelligence:
        """Extract people, places, dates, quotes, and facts using Gemma into structured JSON."""
        system_prompt = (
            "You are the EchoVault Memory Intelligence Agent preserving sacred family oral history. "
            "PHILOSOPHY: Preserve what people actually said. Never manufacture or assume facts. "
            "Do not invent relationships, dates, places, or quotations. If uncertain, mark it explicitly in uncertainty_notes. "
            "Output MUST be valid JSON adhering strictly to the requested schema."
        )

        prompt = f"""
Analyze this personal oral history recorded by narrator: "{narrator}".

STORY CONTENT:
\"\"\"{raw_story}\"\"\"

Produce a JSON object with this exact structure:
{{
  "title": "A short, respectful, evocative title for this memory",
  "summary": "A 2-3 sentence factual summary preserving the exact spirit and details spoken",
  "people": [
    {{"name": "Full or first name mentioned", "relationship": "Relationship to narrator ONLY if stated in text, else null", "context": "Brief context"}}
  ],
  "places": [
    {{"name": "Place name mentioned", "location_type": "city, farm, country, building, etc.", "context": "Context"}}
  ],
  "dates": [
    {{"raw_date": "Exact temporal phrase as spoken (e.g. 1952, Summer of '68)", "iso_year": 1952, "is_approximate": false}}
  ],
  "quotes": [
    {{"quote_text": "Exact words or memorable phrase spoken in the story", "speaker": "Speaker name if explicitly identified"}}
  ],
  "themes": ["list of thematic keywords, e.g. military, farming, childhood"],
  "topics": ["list of specific subjects discussed"],
  "explicit_facts": ["distinct factual assertions stated without doubt"],
  "uncertainty_notes": ["points where narrator expressed hesitation or uncertainty (e.g. 'I think', 'maybe', 'not sure')"]
}}
"""

        try:
            response_text = self.call_ollama(prompt, system_prompt=system_prompt, format_json=True)
            data = self._extract_json_block(response_text)
            if not data:
                raise GemmaServiceError("Model did not return parsable JSON.")
            return MemoryIntelligence.model_validate(data)
        except Exception as e:
            logger.warning(f"Gemma extraction failed or fell back: {e}")
            # Graceful degraded fallback: produce deterministic heuristic intelligence
            # This satisfies: "If Gemma is unavailable, allow text capture, archival, and basic keyword search."
            return self._heuristic_fallback_intelligence(raw_story, narrator, str(e))

    def _heuristic_fallback_intelligence(self, raw_story: str, narrator: str, error_detail: str) -> MemoryIntelligence:
        """Heuristic fallback to guarantee story preservation when AI engine is unavailable."""
        first_line = raw_story.strip().split("\n")[0][:60]
        title = first_line.rstrip(".") if first_line else "Preserved Family Memory"
        summary = (raw_story[:280] + "...") if len(raw_story) > 280 else raw_story
        
        # Simple extraction of possible capitalized names or years
        years = re.findall(r"\b(18\d{2}|19\d{2}|20\d{2})\b", raw_story)
        dates = [{"raw_date": yr, "iso_year": int(yr), "is_approximate": False} for yr in set(years)]

        return MemoryIntelligence(
            title=title,
            summary=summary,
            people=[],
            places=[],
            dates=dates,  # type: ignore
            quotes=[],
            themes=["family history", "archived memory"],
            topics=["personal account"],
            explicit_facts=["Story preserved directly in vault."],
            uncertainty_notes=[f"AI extraction offline ({error_detail}). Original story preserved faithfully."],
        )

    def answer_question_grounded(self, question: str, retrieved_passages: list[RetrievedPassage]) -> GroundedAnswer:
        """Answer a user question using strictly the retrieved memory passages."""
        if not retrieved_passages:
            return GroundedAnswer(
                question=question,
                answer="I couldn't find this information in your saved memories.",
                citations=[],
                supporting_memory_titles=[],
                is_abstention=True,
                abstention_reason="No matching memories or relevant evidence were found in your vault.",
            )

        # Build evidence context block
        evidence_text = "\n\n".join([
            f"[Source Memory: {p.title} | Narrator: {p.narrator or 'Unknown'} | Date: {p.event_date or 'Undated'}]\n"
            f"Passage: {p.passage}"
            for p in retrieved_passages
        ])

        system_prompt = (
            "You are the EchoVault Remembrance Agent. "
            "CORE DIRECTIVE: Answer the question using ONLY the provided memory evidence passages. "
            "Never invent details, dates, relationships, or names not present in the evidence. "
            "If the evidence does NOT contain the answer, you MUST respond exactly: "
            "\"I couldn't find this information in your saved memories.\""
        )

        prompt = f"""
EVIDENCE FROM ARCHIVED MEMORIES:
\"\"\"{evidence_text}\"\"\"

USER QUESTION:
\"{question}\"

INSTRUCTIONS:
1. Ground your answer entirely in the evidence above.
2. If the memories do not state the answer, reply: "I couldn't find this information in your saved memories."
3. Cite the memory title that supports your answer.
4. Keep the answer clear, respectful, and direct.
"""

        try:
            raw_response = self.call_ollama(prompt, system_prompt=system_prompt, format_json=False)
            clean_answer = raw_response.strip()

            # Check for abstention cues
            is_abstention = (
                "couldn't find this information" in clean_answer.lower()
                or "could not find this information" in clean_answer.lower()
                or "not mentioned in the" in clean_answer.lower()
            )

            titles = [p.title for p in retrieved_passages]
            return GroundedAnswer(
                question=question,
                answer=clean_answer,
                citations=retrieved_passages if not is_abstention else [],
                supporting_memory_titles=titles if not is_abstention else [],
                is_abstention=is_abstention,
                uncertainty_disclosure="Grounded strictly in archived evidence." if not is_abstention else "Information absent from archive.",
            )
        except Exception as e:
            # Deterministic fallback when model is unreachable
            return self._deterministic_grounded_answer(question, retrieved_passages, str(e))

    def _deterministic_grounded_answer(
        self, question: str, retrieved_passages: list[RetrievedPassage], error_msg: str
    ) -> GroundedAnswer:
        """Deterministic answer formatter when AI inference is unavailable."""
        if not retrieved_passages:
            return GroundedAnswer(
                question=question,
                answer="I couldn't find this information in your saved memories.",
                citations=[],
                supporting_memory_titles=[],
                is_abstention=True,
                abstention_reason="No matching memories found in your vault.",
            )

        query_words = [w.lower() for w in re.findall(r"\w+", question) if len(w) > 2]
        query_non_stop = [
            w for w in query_words
            if w not in {"what", "where", "when", "who", "why", "how", "did", "was", "were", "the", "about", "our", "their", "tell"}
        ]
        
        combined_text = " ".join([p.passage.lower() + " " + p.title.lower() for p in retrieved_passages])
        has_overlap = any(kw in combined_text for kw in (query_non_stop or query_words))

        if not has_overlap:
            return GroundedAnswer(
                question=question,
                answer="I couldn't find this information in your saved memories.",
                citations=[],
                supporting_memory_titles=[],
                is_abstention=True,
                abstention_reason="No matching facts or keywords found in preserved memories.",
            )

        top_passage = retrieved_passages[0]
        answer_text = (
            f"Based directly on the archived memory '{top_passage.title}' (narrated by {top_passage.narrator}):\n\n"
            f"\"{top_passage.passage}\""
        )
        return GroundedAnswer(
            question=question,
            answer=answer_text,
            citations=retrieved_passages[:3],
            supporting_memory_titles=[p.title for p in retrieved_passages[:3]],
            is_abstention=False,
            uncertainty_disclosure=f"Retrieved via keyword search (LLM offline: {error_msg}). Passages shown verbatim.",
        )


gemma_service = GemmaService()
