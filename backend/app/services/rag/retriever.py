from typing import List, Optional
from sqlalchemy.orm import Session
from app.services.rag.embeddings import EmbeddingService
from app.services.rag.vector_store import VectorStoreAdapter, ScoredChunkResult

class KnowledgeRetriever:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStoreAdapter(db)

    async def retrieve_for_ticket(
        self,
        title: str,
        description: str,
        affected_service: str,
        category: str,
        error_logs: Optional[str] = None,
        top_k: int = 4
    ) -> List[ScoredChunkResult]:
        """
        Constructs rich operational retrieval query from ticket symptoms and searches vector store.
        """
        query_terms = [title, description]
        if error_logs:
            # Include first few lines of error logs
            clean_logs = error_logs.strip().split("\n")[:3]
            query_terms.extend(clean_logs)
            
        full_query = " ".join(query_terms)
        query_vector = await self.embedding_service.get_embedding(full_query)

        return self.vector_store.search_hybrid(
            query=full_query,
            query_vector=query_vector,
            top_k=top_k,
            service_filter=affected_service,
            category_filter=category,
            min_relevance_threshold=0.35
        )

    async def search_query(
        self,
        query: str,
        service: Optional[str] = None,
        category: Optional[str] = None,
        top_k: int = 5
    ) -> List[ScoredChunkResult]:
        query_vector = await self.embedding_service.get_embedding(query)
        return self.vector_store.search_hybrid(
            query=query,
            query_vector=query_vector,
            top_k=top_k,
            service_filter=service,
            category_filter=category,
            min_relevance_threshold=0.30
        )
