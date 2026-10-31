"""Agent 3 — Memory Intelligence Agent: Extracts structured entities and quotes via Gemma."""

import time
from echovault.schemas import OrchestratorMemoryState, ExecutionStepTrace, ProcessingStatus
from echovault.services.gemma_service import gemma_service


class MemoryIntelligenceAgent:
    name: str = "Memory Intelligence Agent"

    def process(self, state: OrchestratorMemoryState) -> OrchestratorMemoryState:
        """Call Gemma to analyze story, extract entities, quotes, themes, and detect uncertainties."""
        start_time = time.time()
        narrator = state.narrator or "Family Member"
        content = state.raw_content

        if not content or not content.strip():
            state.errors.append("Cannot extract intelligence: story text is empty.")
            state.processing_status = ProcessingStatus.FAILED
            return state

        intelligence = gemma_service.extract_memory_intelligence(content, narrator=narrator)
        state.intelligence = intelligence

        duration_ms = (time.time() - start_time) * 1000
        state.traces.append(ExecutionStepTrace(
            agent_name=self.name,
            stage="intelligence_extraction",
            status="completed",
            duration_ms=round(duration_ms, 2),
            message=(
                f"Extracted {len(intelligence.people)} people, {len(intelligence.places)} places, "
                f"{len(intelligence.quotes)} quotes, and {len(intelligence.themes)} themes."
            ),
        ))
        return state


memory_intelligence_agent = MemoryIntelligenceAgent()
