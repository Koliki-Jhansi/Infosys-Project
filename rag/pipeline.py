"""
AeroAssist AI - RAG Context Builder & Resolution Pipeline
Builds grounded context from retrieved airport support articles and generates
structured domain-specific passenger resolutions.
"""
from typing import Dict, Optional, List
from .retriever import get_retriever, AirportRetriever

class RAGPipeline:
    def __init__(self, retriever: Optional[AirportRetriever] = None):
        self.retriever = retriever or get_retriever()

    def process_query(self, title: str, description: str, category: str = "", metadata: Optional[Dict] = None) -> Dict:
        """
        Executes end-to-end RAG workflow:
        Ticket Query -> Vector Retrieval -> Context Construction -> Grounded Resolution.
        """
        query_text = f"{title} {description} {category}".strip()
        retrieval_res = self.retriever.retrieve(query_text, top_k=3)

        knowledge_found = retrieval_res["knowledge_found"]
        top_article = retrieval_res["top_article"]
        similarity_score = retrieval_res["similarity_score"]
        ranked_articles = retrieval_res["ranked_articles"]

        # Build Context
        context_str = self._build_context(retrieval_res)

        # Generate Grounded Resolution
        resolution_data = self._generate_resolution(
            title=title,
            description=description,
            category=category,
            retrieval_res=retrieval_res,
            metadata=metadata or {}
        )

        return {
            "query": query_text,
            "knowledge_found": knowledge_found,
            "top_article": top_article,
            "similarity_score": similarity_score,
            "ranked_articles": ranked_articles,
            "context": context_str,
            "resolution_text": resolution_data["resolution_text"],
            "resolution_steps": resolution_data["resolution_steps"],
            "resolution_completeness": resolution_data["resolution_completeness"]
        }

    def _build_context(self, retrieval_res: Dict) -> str:
        """Formats retrieved articles into grounded context."""
        if not retrieval_res["knowledge_found"] or not retrieval_res["ranked_articles"]:
            return "No relevant airport knowledge articles met the relevance threshold."

        lines = ["=== AIRPORT KNOWLEDGE CONTEXT ==="]
        for idx, art in enumerate(retrieval_res["ranked_articles"], 1):
            lines.append(f"\n[Source {idx}: {art['id']} - {art['title']}] (Similarity: {art['similarity_score']:.2f})")
            lines.append(f"Category: {art['category']} | Cluster: {art['cluster']}")
            lines.append(f"Content: {art['content']}")
        return "\n".join(lines)

    def _generate_resolution(self, title: str, description: str, category: str, retrieval_res: Dict, metadata: Dict) -> Dict:
        """
        Generates passenger-friendly resolution based strictly on retrieved knowledge procedures.
        Does NOT hallucinate live flight status, gate changes, refund approval, or operational decisions.
        """
        if not retrieval_res["knowledge_found"] or not retrieval_res["top_article"]:
            # Fallback when no KB article matches
            return {
                "resolution_text": (
                    "We have reviewed your support request regarding "
                    f"'{title}'. However, no standard automated airport support procedure sufficiently matches your specific inquiry. "
                    "To ensure accurate and safe assistance, this inquiry will be routed to a human passenger support specialist."
                ),
                "resolution_steps": [
                    "A human customer care agent will review your travel details.",
                    "An airline support specialist will follow up with verified operational instructions."
                ],
                "resolution_completeness": 0.20
            }

        top_art = retrieval_res["top_article"]
        art_id = top_art["id"]
        art_title = top_art["title"]
        art_content = top_art["content"]

        # Parse actionable steps from knowledge content
        steps = self._extract_actionable_steps(art_content, metadata)

        # Passenger-facing resolution format
        resolution_text = (
            f"Thank you for contacting AeroAssist Passenger Support. We identified your issue as a "
            f"{top_art['category']} request relating to '{art_title}' (Reference: {art_id}).\n\n"
            f"Official Support Guidance:\n{art_content}\n\n"
            f"Recommended Action Steps:\n" + "\n".join([f"{i+1}. {step}" for i, step in enumerate(steps)]) +
            f"\n\nIf your issue is not resolved after following these steps, our airport customer service team will provide further on-ground assistance."
        )

        # Resolution completeness is high when grounded in matching KB article
        completeness = 0.95 if retrieval_res["similarity_score"] >= 0.40 else 0.85

        return {
            "resolution_text": resolution_text,
            "resolution_steps": steps,
            "resolution_completeness": round(completeness, 2)
        }

    def _extract_actionable_steps(self, content: str, metadata: Dict) -> List[str]:
        """Extracts concise procedural guidance steps from content."""
        sentences = [s.strip() for s in content.split(".") if len(s.strip()) > 15]
        steps = []
        for s in sentences[:3]:
            steps.append(f"{s}.")
        
        flight_num = metadata.get("flight_number")
        if flight_num and not any(flight_num in step for step in steps):
            steps.append(f"Keep your flight details ({flight_num}) and boarding documentation accessible for airport verification.")
        else:
            steps.append("Have your booking reference and valid photo identification ready at the airport counter.")

        return steps


# Global singleton instance
_pipeline_instance = None

def get_rag_pipeline() -> RAGPipeline:
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = RAGPipeline()
    return _pipeline_instance
