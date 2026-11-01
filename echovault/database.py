"""SQLite database engine with FTS5 search, WAL mode, foreign keys, and audit logging."""

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from echovault.config import config
from echovault.schemas import (
    MemoryRecord,
    MemorySource,
    ExtractedPerson,
    ExtractedPlace,
    ExtractedQuote,
    ProcessingStatus,
    SourceType,
    RetrievedPassage,
    AuditEvent,
    AuditAction,
)


class Database:
    def __init__(self, db_path: Path = config.db_path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Create a connection with foreign keys and row factory enabled."""
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    def init_db(self) -> None:
        """Initialize normalized schema, indexes, and FTS5 search table."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. memories core table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                summary TEXT,
                narrator TEXT DEFAULT 'Family Member',
                event_date_raw TEXT,
                event_date_iso TEXT,
                uncertainty_notes TEXT,
                processing_status TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                source_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # 2. memory sources (file & recording provenance)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_sources (
                id TEXT PRIMARY KEY,
                memory_id TEXT NOT NULL,
                source_type TEXT NOT NULL,
                original_filename TEXT,
                file_path TEXT,
                mime_type TEXT,
                file_size_bytes INTEGER DEFAULT 0,
                duration_seconds REAL,
                content_sha256 TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
            );
            """)

            # 3. transcripts
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS transcripts (
                id TEXT PRIMARY KEY,
                memory_id TEXT NOT NULL,
                raw_text TEXT NOT NULL,
                edited_text TEXT,
                whisper_model TEXT,
                confidence_score REAL,
                timestamps_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
            );
            """)

            # 4. people entity catalog
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS people (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                relationship TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name, relationship)
            );
            """)

            # 5. places entity catalog
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS places (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                location_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # 6. memory entities link table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_entities (
                id TEXT PRIMARY KEY,
                memory_id TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_name TEXT NOT NULL,
                secondary_value TEXT,
                context_passage TEXT,
                confidence REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
            );
            """)

            # 7. memory tags / themes
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_tags (
                id TEXT PRIMARY KEY,
                memory_id TEXT NOT NULL,
                tag TEXT NOT NULL,
                tag_type TEXT DEFAULT 'theme',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE,
                UNIQUE(memory_id, tag, tag_type)
            );
            """)

            # 8. memory processing runs
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_processing_runs (
                id TEXT PRIMARY KEY,
                memory_id TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                stage TEXT NOT NULL,
                status TEXT NOT NULL,
                duration_ms REAL NOT NULL,
                message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
            );
            """)

            # 9. memory audit events
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_audit_events (
                id TEXT PRIMARY KEY,
                memory_id TEXT,
                action TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                details_json TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_content_hash ON memories(content_hash);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_created_at ON memories(created_at);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_memory ON memory_entities(memory_id);")

            # 10. FTS5 Virtual Table for full-text search
            cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                id UNINDEXED,
                title,
                content,
                summary,
                narrator,
                tokenize = 'porter unicode61'
            );
            """)

            conn.commit()

    # -------------------------------------------------------------
    # Memory Operations
    # -------------------------------------------------------------

    def find_duplicate_by_hash(self, content_hash: str) -> Optional[str]:
        """Check if an exact matching memory content hash already exists."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM memories WHERE content_hash = ? LIMIT 1", (content_hash,))
            row = cursor.fetchone()
            return row["id"] if row else None

    def insert_memory_record(
        self,
        record: MemoryRecord,
        source: Optional[MemorySource] = None,
        entities: Optional[List[Dict[str, Any]]] = None,
        themes: Optional[List[str]] = None,
        quotes: Optional[List[ExtractedQuote]] = None,
    ) -> str:
        """Insert a full memory record atomically in a transaction."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now_iso = datetime.utcnow().isoformat()

            cursor.execute("""
            INSERT INTO memories (
                id, title, content, summary, narrator,
                event_date_raw, event_date_iso, uncertainty_notes,
                processing_status, content_hash, source_type, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.id,
                record.title,
                record.content,
                record.summary or "",
                record.narrator or "Family Member",
                record.event_date_raw,
                record.event_date_iso,
                record.uncertainty_notes,
                record.processing_status.value if hasattr(record.processing_status, "value") else str(record.processing_status),
                record.content_hash,
                record.source_type.value if hasattr(record.source_type, "value") else str(record.source_type),
                now_iso,
                now_iso,
            ))

            # Sync to FTS5
            cursor.execute("""
            INSERT INTO memories_fts (id, title, content, summary, narrator)
            VALUES (?, ?, ?, ?, ?)
            """, (
                record.id,
                record.title,
                record.content,
                record.summary or "",
                record.narrator or "Family Member",
            ))

            # Insert Source
            if source:
                cursor.execute("""
                INSERT INTO memory_sources (
                    id, memory_id, source_type, original_filename,
                    file_path, mime_type, file_size_bytes, duration_seconds,
                    content_sha256, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    source.id,
                    source.memory_id,
                    source.source_type.value if hasattr(source.source_type, "value") else str(source.source_type),
                    source.original_filename,
                    str(source.file_path) if source.file_path else None,
                    source.mime_type,
                    source.file_size_bytes,
                    source.duration_seconds,
                    source.content_sha256,
                    now_iso,
                ))

            # Insert Entities
            if entities:
                for ent in entities:
                    cursor.execute("""
                    INSERT INTO memory_entities (
                        id, memory_id, entity_type, entity_name,
                        secondary_value, context_passage, confidence, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(uuid.uuid4()),
                        record.id,
                        ent.get("type", "entity"),
                        ent.get("name", ""),
                        ent.get("secondary_value"),
                        ent.get("context"),
                        ent.get("confidence", 1.0),
                        now_iso,
                    ))

            # Insert Themes
            if themes:
                for t in themes:
                    cursor.execute("""
                    INSERT OR IGNORE INTO memory_tags (id, memory_id, tag, tag_type, created_at)
                    VALUES (?, ?, ?, 'theme', ?)
                    """, (str(uuid.uuid4()), record.id, t.strip().lower(), now_iso))

            # Insert Quotes
            if quotes:
                for q in quotes:
                    cursor.execute("""
                    INSERT INTO memory_entities (
                        id, memory_id, entity_type, entity_name,
                        secondary_value, context_passage, confidence, created_at
                    ) VALUES (?, ?, 'quote', ?, ?, ?, 1.0, ?)
                    """, (
                        str(uuid.uuid4()),
                        record.id,
                        q.quote_text,
                        q.speaker,
                        None,
                        now_iso,
                    ))

            conn.commit()
            return record.id

    def update_memory_status(self, memory_id: str, status: ProcessingStatus, summary: Optional[str] = None) -> None:
        """Update processing status and summary for a memory."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if summary:
                cursor.execute("""
                UPDATE memories SET processing_status = ?, summary = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """, (status.value, summary, memory_id))
                # Update FTS5 summary
                cursor.execute("UPDATE memories_fts SET summary = ? WHERE id = ?", (summary, memory_id))
            else:
                cursor.execute("""
                UPDATE memories SET processing_status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """, (status.value, memory_id))
            conn.commit()

    def get_memory(self, memory_id: str) -> Optional[MemoryRecord]:
        """Fetch a single memory with its associated entities."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
            row = cursor.fetchone()
            if not row:
                return None

            # Fetch entities
            cursor.execute("SELECT * FROM memory_entities WHERE memory_id = ?", (memory_id,))
            ent_rows = cursor.fetchall()
            
            people: List[ExtractedPerson] = []
            places: List[ExtractedPlace] = []
            quotes: List[ExtractedQuote] = []
            
            for er in ent_rows:
                etype = er["entity_type"]
                if etype == "person":
                    people.append(ExtractedPerson(
                        name=er["entity_name"],
                        relationship=er["secondary_value"],
                        context=er["context_passage"]
                    ))
                elif etype == "place":
                    places.append(ExtractedPlace(
                        name=er["entity_name"],
                        location_type=er["secondary_value"],
                        context=er["context_passage"]
                    ))
                elif etype == "quote":
                    quotes.append(ExtractedQuote(
                        quote_text=er["entity_name"],
                        speaker=er["secondary_value"]
                    ))

            # Fetch themes
            cursor.execute("SELECT tag FROM memory_tags WHERE memory_id = ?", (memory_id,))
            themes = [r["tag"] for r in cursor.fetchall()]

            return MemoryRecord(
                id=row["id"],
                title=row["title"],
                content=row["content"],
                summary=row["summary"],
                narrator=row["narrator"],
                event_date_raw=row["event_date_raw"],
                event_date_iso=row["event_date_iso"],
                uncertainty_notes=row["uncertainty_notes"],
                processing_status=ProcessingStatus(row["processing_status"]),
                content_hash=row["content_hash"],
                source_type=SourceType(row["source_type"]),
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.utcnow(),
                updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else datetime.utcnow(),
                people=people,
                places=places,
                themes=themes,
                quotes=quotes,
            )

    def list_memories(self, limit: int = 50, offset: int = 0) -> List[MemoryRecord]:
        """List memories in reverse chronological order."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id FROM memories ORDER BY created_at DESC LIMIT ? OFFSET ?
            """, (limit, offset))
            rows = cursor.fetchall()
            return [self.get_memory(r["id"]) for r in rows if r["id"]]

    def count_memories(self) -> int:
        """Count total memories in the vault."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS total FROM memories")
            return cursor.fetchone()["total"]

    def delete_memory(self, memory_id: str) -> bool:
        """Safely delete a memory and its associated records and FTS entries."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # FTS cleanup
            cursor.execute("DELETE FROM memories_fts WHERE id = ?", (memory_id,))
            # Cascade deletes take care of related tables
            cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted

    # -------------------------------------------------------------
    # Full-Text Search (FTS5)
    # -------------------------------------------------------------

    STOP_WORDS = {
        "a", "about", "an", "and", "are", "as", "at", "be", "by", "did", "do",
        "does", "for", "from", "how", "in", "is", "it", "me", "my", "of", "on",
        "or", "our", "tell", "that", "the", "their", "there", "this", "to",
        "was", "we", "were", "what", "when", "where", "who", "will", "with", "would"
    }

    def search_memories(self, query_text: str, limit: int = 10) -> List[RetrievedPassage]:
        """Search memory title, content, summary, and narrator using SQLite FTS5."""
        if not query_text or not query_text.strip():
            return []

        # Sanitize query for FTS5 (avoid syntax errors with unmatched quotes/operators)
        safe_query = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in query_text).strip()
        if not safe_query:
            return []

        words = [w.lower() for w in safe_query.split() if len(w) > 1]
        meaningful_words = [w for w in words if w not in self.STOP_WORDS]
        chosen_tokens = meaningful_words if meaningful_words else words

        if not chosen_tokens:
            return []

        tokens = [f'"{tok}"' for tok in chosen_tokens]
        match_expr = " OR ".join(tokens)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                SELECT 
                    m.id,
                    m.title,
                    m.content,
                    m.summary,
                    m.narrator,
                    m.event_date_raw,
                    bm25(memories_fts) AS rank_score,
                    snippet(memories_fts, 2, '<b>', '</b>', '...', 35) AS snippet_passage
                FROM memories_fts f
                JOIN memories m ON f.id = m.id
                WHERE memories_fts MATCH ?
                ORDER BY rank_score ASC
                LIMIT ?
                """, (match_expr, limit))
                rows = cursor.fetchall()

                results: List[RetrievedPassage] = []
                for r in rows:
                    raw_score = r["rank_score"]
                    norm_score = round(max(0.1, 10.0 / (1.0 + abs(raw_score))), 2)
                    
                    # Provide full narrative context when concise, otherwise clean snippet
                    full_content = r["content"]
                    if len(full_content) <= 800:
                        passage = full_content
                    else:
                        passage = (r["snippet_passage"] or full_content[:400] + "...").replace("<b>", "").replace("</b>", "")

                    results.append(RetrievedPassage(
                        memory_id=r["id"],
                        title=r["title"],
                        passage=passage,
                        narrator=r["narrator"],
                        event_date=r["event_date_raw"],
                        relevance_score=norm_score,
                    ))
                return results
            except sqlite3.OperationalError:
                # Fallback to standard LIKE search if FTS5 parser encounters edge case
                return self._fallback_like_search(safe_query, limit)

    def _fallback_like_search(self, query: str, limit: int = 10) -> List[RetrievedPassage]:
        """Fallback LIKE search when FTS5 experiences query parsing issues."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, title, content, summary, narrator, event_date_raw
            FROM memories
            WHERE title LIKE ? OR content LIKE ? OR summary LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
            """, (f"%{query}%", f"%{query}%", f"%{query}%", limit))
            rows = cursor.fetchall()
            return [
                RetrievedPassage(
                    memory_id=r["id"],
                    title=r["title"],
                    passage=r["content"][:250] + "...",
                    narrator=r["narrator"],
                    event_date=r["event_date_raw"],
                    relevance_score=1.0,
                )
                for r in rows
            ]

    # -------------------------------------------------------------
    # Audit & Tracing
    # -------------------------------------------------------------

    def record_audit_event(self, event: AuditEvent) -> None:
        """Persist an audit trail event for traceability and privacy."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO memory_audit_events (id, memory_id, action, agent_name, details_json, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                event.memory_id,
                event.action.value if hasattr(event.action, "value") else str(event.action),
                event.agent_name,
                json.dumps(event.details),
                event.timestamp.isoformat(),
            ))
            conn.commit()

    def get_audit_trail(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent audit events."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM memory_audit_events ORDER BY timestamp DESC LIMIT ?
            """, (limit,))
            return [dict(r) for r in cursor.fetchall()]

    def get_timeline_memories(self) -> List[Dict[str, Any]]:
        """Retrieve all memories with dates for timeline chronological ordering."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, title, narrator, event_date_raw, event_date_iso, summary, created_at
            FROM memories
            ORDER BY 
                CASE WHEN event_date_iso IS NOT NULL AND event_date_iso != '' THEN event_date_iso ELSE created_at END ASC
            """)
            return [dict(r) for r in cursor.fetchall()]

    def get_all_entities_grouped(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get people and places for entity browsing."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT entity_type, entity_name, secondary_value, COUNT(DISTINCT memory_id) as memory_count
            FROM memory_entities
            WHERE entity_type IN ('person', 'place')
            GROUP BY entity_type, entity_name, secondary_value
            ORDER BY memory_count DESC, entity_name ASC
            """)
            rows = cursor.fetchall()
            grouped: Dict[str, List[Dict[str, Any]]] = {"people": [], "places": []}
            for r in rows:
                if r["entity_type"] == "person":
                    grouped["people"].append(dict(r))
                elif r["entity_type"] == "place":
                    grouped["places"].append(dict(r))
            return grouped


db = Database()
