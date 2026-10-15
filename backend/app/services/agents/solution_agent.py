from typing import Dict, Any, Tuple
from app.services.agents.base import BaseAgent
from app.services.rag.grounding import GroundedSolutionService
from app.services.rag.vector_store import ScoredChunkResult

class SolutionGenerationAgent(BaseAgent):
    def __init__(self):
        super().__init__("Solution Generation Agent")
        self.grounding_service = GroundedSolutionService()

    async def run(self, state: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
        ticket = state.get("ticket", {})
        classification = state.get("classification", {})
        retrieval = state.get("retrieval", {})
        rca = state.get("root_cause_analysis", {})
        sources_data = retrieval.get("sources", [])

        # Convert back to ScoredChunkResults for grounding synthesis
        chunks = []
        for s in sources_data:
            chunks.append(
                ScoredChunkResult(
                    chunk_id=s.get("chunk_id", 0),
                    document_id=s.get("document_id", 0),
                    document_title=s.get("document_title", "Unknown"),
                    service=s.get("service", ""),
                    category=s.get("category", ""),
                    doc_type=s.get("doc_type", "Guide"),
                    chunk_index=s.get("chunk_index", 0),
                    content=s.get("content", ""),
                    semantic_score=s.get("similarity_score", 0.0) / 100.0,
                    keyword_score=0.5,
                    combined_score=s.get("similarity_score", 0.0) / 100.0
                )
            )

        solution = self.grounding_service.generate_grounded_solution(
            ticket_id=ticket.get("id", 0),
            title=ticket.get("title", ""),
            description=ticket.get("description", ""),
            affected_service=ticket.get("affected_service", ""),
            category=ticket.get("category", ""),
            priority=classification.get("priority", "P3 Medium"),
            retrieved_chunks=chunks
        )

        outputs = solution.model_dump()

        updated_state = {
            **state,
            "solution": outputs
        }

        return "COMPLETED", outputs, updated_state
