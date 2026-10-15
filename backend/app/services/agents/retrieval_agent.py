from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.services.agents.base import BaseAgent
from app.services.rag.retriever import KnowledgeRetriever

class KnowledgeRetrievalAgent(BaseAgent):
    def __init__(self, db: Session):
        super().__init__("Knowledge Retrieval Agent")
        self.db = db

    async def run(self, state: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
        ticket = state.get("ticket", {})
        title = ticket.get("title", "")
        description = ticket.get("description", "")
        service = ticket.get("affected_service", "")
        category = ticket.get("category", "")
        error_logs = ticket.get("error_logs", "")

        retriever = KnowledgeRetriever(self.db)
        chunks = await retriever.retrieve_for_ticket(
            title=title,
            description=description,
            affected_service=service,
            category=category,
            error_logs=error_logs,
            top_k=4
        )

        sources = []
        for ch in chunks:
            sources.append({
                "document_id": ch.document_id,
                "document_title": ch.document_title,
                "service": ch.service,
                "category": ch.category,
                "doc_type": ch.doc_type,
                "chunk_index": ch.chunk_index,
                "similarity_score": round(ch.combined_score * 100, 1),
                "content": ch.content
            })

        evidence_sufficient = len(sources) > 0 and sources[0]["similarity_score"] >= 40.0

        outputs = {
            "evidence_found": len(sources) > 0,
            "evidence_sufficient": evidence_sufficient,
            "top_similarity_score": sources[0]["similarity_score"] if sources else 0.0,
            "retrieved_sources_count": len(sources),
            "sources": sources,
            "retrieval_notes": f"Retrieved {len(sources)} grounded knowledge chunks." if evidence_sufficient else "Insufficient grounded knowledge found in repository."
        }

        updated_state = {
            **state,
            "retrieval": outputs
        }

        return "COMPLETED", outputs, updated_state
