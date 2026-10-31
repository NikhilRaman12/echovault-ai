"""Agent 4 — Memory Archivist Agent: Persists memories, records provenance, prevents duplicate submission."""

import time
from typing import Optional
from echovault.database import db
from echovault.schemas import (
    OrchestratorMemoryState,
    MemoryRecord,
    MemorySource,
    ProcessingStatus,
    ExecutionStepTrace,
    AuditEvent,
    AuditAction,
)
from echovault.services.storage_service import storage_service


class MemoryArchivistAgent:
    name: str = "Memory Archivist Agent"

    def process(
        self,
        state: OrchestratorMemoryState,
        source_record: Optional[MemorySource] = None,
    ) -> OrchestratorMemoryState:
        """Persist memory to SQLite with full relational and FTS5 indexing."""
        start_time = time.time()
        content = state.raw_content.strip()
        content_hash = storage_service.compute_sha256(content)

        # Check duplicate
        existing_id = db.find_duplicate_by_hash(content_hash)
        if existing_id:
            state.errors.append(f"Duplicate detected: memory content already exists under ID {existing_id}.")
            state.processing_status = ProcessingStatus.FAILED
            duration_ms = (time.time() - start_time) * 1000
            state.traces.append(ExecutionStepTrace(
                agent_name=self.name,
                stage="deduplication_check",
                status="rejected_duplicate",
                duration_ms=round(duration_ms, 2),
                message=f"Duplicate submission blocked. Existing ID: {existing_id}",
            ))
            return state

        # Prepare memory record
        title = "Preserved Family Story"
        summary = ""
        event_date_raw = None
        event_date_iso = None
        uncertainty_notes = None

        if state.intelligence:
            title = state.intelligence.title or title
            summary = state.intelligence.summary or ""
            if state.intelligence.dates:
                event_date_raw = state.intelligence.dates[0].raw_date
                if state.intelligence.dates[0].iso_year:
                    event_date_iso = str(state.intelligence.dates[0].iso_year)
            if state.intelligence.uncertainty_notes:
                uncertainty_notes = "; ".join(state.intelligence.uncertainty_notes)

        record = MemoryRecord(
            id=state.memory_id,
            title=title,
            content=content,
            summary=summary,
            narrator=state.narrator or "Family Member",
            event_date_raw=event_date_raw,
            event_date_iso=event_date_iso,
            uncertainty_notes=uncertainty_notes,
            processing_status=ProcessingStatus.COMPLETED,
            content_hash=content_hash,
            source_type=state.source_type,
            people=state.intelligence.people if state.intelligence else [],
            places=state.intelligence.places if state.intelligence else [],
            themes=state.intelligence.themes if state.intelligence else [],
            quotes=state.intelligence.quotes if state.intelligence else [],
        )

        # Build entities list for DB
        entities = []
        if state.intelligence:
            for p in state.intelligence.people:
                entities.append({
                    "type": "person",
                    "name": p.name,
                    "secondary_value": p.relationship,
                    "context": p.context,
                })
            for pl in state.intelligence.places:
                entities.append({
                    "type": "place",
                    "name": pl.name,
                    "secondary_value": pl.location_type,
                    "context": pl.context,
                })

        db.insert_memory_record(
            record=record,
            source=source_record,
            entities=entities,
            themes=record.themes,
            quotes=record.quotes,
        )

        db.record_audit_event(AuditEvent(
            memory_id=record.id,
            action=AuditAction.ARCHIVED,
            agent_name=self.name,
            details={
                "title": record.title,
                "source_type": record.source_type.value,
                "content_length": len(content),
            },
        ))

        state.archived_record = record
        state.processing_status = ProcessingStatus.COMPLETED

        duration_ms = (time.time() - start_time) * 1000
        state.traces.append(ExecutionStepTrace(
            agent_name=self.name,
            stage="archival_commit",
            status="success",
            duration_ms=round(duration_ms, 2),
            message=f"Memory safely archived and indexed with ID {record.id}.",
        ))
        return state


archivist_agent = MemoryArchivistAgent()
