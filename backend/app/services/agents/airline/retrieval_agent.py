from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.services.agents.base import BaseAgent
from app.services.rag.retriever import KnowledgeRetriever

class AirlineRetrievalAgent(BaseAgent):
    def __init__(self, db: Session, name: str = "Retrieval Agent"):
        super().__init__(name=name)
        self.db = db

    async def run(self, state: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
        ticket = state.get("ticket", {})
        diagnosis = state.get("diagnosis", {})
        
        title = ticket.get("title", "") or ticket.get("subject", "")
        description = ticket.get("description", "")
        category = diagnosis.get("category") or ticket.get("category", "")
        keywords = diagnosis.get("detected_keywords", [])

        # Formulate search query
        query_parts = [title]
        if keywords:
            query_parts.extend(keywords[:3])
        query = " ".join(query_parts)

        retriever = KnowledgeRetriever(self.db)
        results = await retriever.search_query(
            query=query,
            category=category if category != "Other" else None,
            top_k=4
        )

        sources = []
        for r in results:
            sources.append({
                "chunk_id": r.chunk_id,
                "document_id": r.document_id,
                "document_title": r.document_title,
                "category": r.category,
                "relevance_score": round(r.combined_score, 3),
                "similarity_percentage": round(r.combined_score * 100, 1),
                "excerpt": r.content[:350] + ("..." if len(r.content) > 350 else "")
            })

        has_sufficient_evidence = len(sources) > 0 and (sources[0]["relevance_score"] >= 0.35)
        top_relevance = sources[0]["relevance_score"] if sources else 0.0

        outputs = {
            "query_used": query,
            "category_filter": category,
            "retrieved_count": len(sources),
            "top_relevance_score": round(top_relevance, 3),
            "has_sufficient_evidence": has_sufficient_evidence,
            "sources": sources
        }

        updated_state = dict(state)
        updated_state["retrieval"] = outputs
        updated_state["sources"] = sources
        updated_state["has_sufficient_evidence"] = has_sufficient_evidence

        return "COMPLETED", outputs, updated_state
