"""Service for exporting and restoring personal family archives in JSON and Markdown formats."""

import json
from datetime import datetime
from typing import Dict, Any, Tuple
from echovault.database import db
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


class ExportService:
    def __init__(self, database=db):
        self.db = database

    def export_archive_to_dict(self) -> Dict[str, Any]:
        """Export all memories, entities, and metadata into a comprehensive dictionary."""
        memories = self.db.list_memories(limit=10000)
        export_payload = {
            "application": "EchoVault AI",
            "version": "0.1.0",
            "exported_at": datetime.utcnow().isoformat(),
            "total_memories": len(memories),
            "memories": [m.model_dump(mode="json") for m in memories],
        }
        
        self.db.record_audit_event(AuditEvent(
            action=AuditAction.ARCHIVE_EXPORTED,
            agent_name="ExportService",
            details={"memories_exported": len(memories)},
        ))
        return export_payload

    def export_archive_to_json(self) -> str:
        """Export archive as a formatted JSON string."""
        data = self.export_archive_to_dict()
        return json.dumps(data, indent=2, ensure_ascii=False)

    def export_archive_to_markdown(self) -> str:
        """Export archive as a beautifully formatted human-readable Markdown book."""
        memories = self.db.list_memories(limit=10000)
        lines = [
            "# EchoVault AI — Family Memory Archive",
            f"*Generated on {datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')}*",
            "",
            "---",
            "",
        ]

        for m in memories:
            lines.append(f"## {m.title}")
            lines.append(f"**Narrator:** {m.narrator or 'Family Member'}  ")
            if m.event_date_raw:
                lines.append(f"**Date:** {m.event_date_raw}  ")
            lines.append(f"**Source Type:** {m.source_type.value}  ")
            lines.append("")
            
            if m.summary:
                lines.append(f"> *{m.summary}*")
                lines.append("")

            lines.append("### Original Recording / Story")
            lines.append(m.content)
            lines.append("")

            if m.people:
                people_strs = [f"{p.name} ({p.relationship})" if p.relationship else p.name for p in m.people]
                lines.append(f"**People Mentioned:** {', '.join(people_strs)}  ")
            if m.places:
                lines.append(f"**Places Mentioned:** {', '.join(p.name for p in m.places)}  ")
            if m.themes:
                lines.append(f"**Themes:** {', '.join(m.themes)}  ")
            if m.quotes:
                lines.append("**Notable Quotes:**")
                for q in m.quotes:
                    spk = f" — {q.speaker}" if q.speaker else ""
                    lines.append(f"- *\"{q.quote_text}\"*{spk}")
                lines.append("")

            if m.uncertainty_notes:
                lines.append(f"**Uncertainty / Notes:** {m.uncertainty_notes}")
                lines.append("")

            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    def restore_archive_from_json(self, json_str: str) -> Tuple[int, int]:
        """
        Restore memories from an exported JSON string.
        Returns: (imported_count, skipped_duplicates_count)
        """
        data = json.loads(json_str)
        memories_data = data.get("memories", [])
        imported = 0
        skipped = 0

        for item in memories_data:
            content_hash = item.get("content_hash")
            if not content_hash:
                import hashlib
                content_hash = hashlib.sha256(item.get("content", "").encode()).hexdigest()

            # Check duplicate
            if self.db.find_duplicate_by_hash(content_hash):
                skipped += 1
                continue

            record = MemoryRecord(
                id=item["id"],
                title=item["title"],
                content=item["content"],
                summary=item.get("summary"),
                narrator=item.get("narrator", "Family Member"),
                event_date_raw=item.get("event_date_raw"),
                event_date_iso=item.get("event_date_iso"),
                uncertainty_notes=item.get("uncertainty_notes"),
                processing_status=ProcessingStatus(item.get("processing_status", "completed")),
                content_hash=content_hash,
                source_type=SourceType(item.get("source_type", "manual_text")),
                people=[ExtractedPerson(**p) for p in item.get("people", [])],
                places=[ExtractedPlace(**pl) for pl in item.get("places", [])],
                themes=item.get("themes", []),
                quotes=[ExtractedQuote(**q) for q in item.get("quotes", [])],
            )

            entities = []
            for p in record.people:
                entities.append({"type": "person", "name": p.name, "secondary_value": p.relationship, "context": p.context})
            for pl in record.places:
                entities.append({"type": "place", "name": pl.name, "secondary_value": pl.location_type, "context": pl.context})

            self.db.insert_memory_record(
                record=record,
                entities=entities,
                themes=record.themes,
                quotes=record.quotes,
            )
            imported += 1

        self.db.record_audit_event(AuditEvent(
            action=AuditAction.ARCHIVE_RESTORED,
            agent_name="ExportService",
            details={"imported": imported, "skipped_duplicates": skipped},
        ))
        return imported, skipped


export_service = ExportService()
