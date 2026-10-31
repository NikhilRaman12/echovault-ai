"""Retrieval service managing FTS5 full-text indexing, snippet ranking, and hybrid search."""

from typing import List
from echovault.database import db
from echovault.schemas import RetrievedPassage


class RetrievalService:
    def __init__(self, database=db):
        self.db = database

    def retrieve_passages(self, query: str, limit: int = 5) -> List[RetrievedPassage]:
        """Search memory vault and return ranked relevant passages."""
        return self.db.search_memories(query, limit=limit)


retrieval_service = RetrievalService()
