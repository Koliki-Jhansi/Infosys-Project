import math
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.knowledge import KnowledgeDocument, DocumentChunk

def compute_cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    similarity = dot / (norm_a * norm_b)
    return max(0.0, min(1.0, float(similarity)))

def compute_keyword_overlap(query: str, text: str) -> float:
    q_words = set(re.findall(r'\b[a-zA-Z0-9_\-]{3,}\b', query.lower()))
    if not q_words:
        return 0.0
    t_words = set(re.findall(r'\b[a-zA-Z0-9_\-]{3,}\b', text.lower()))
    overlap = len(q_words.intersection(t_words))
    return min(1.0, overlap / max(1, len(q_words)))

class ScoredChunkResult:
    def __init__(
        self,
        chunk_id: int,
        document_id: int,
        document_title: str,
        service: str,
        category: str,
        doc_type: str,
        chunk_index: int,
        content: str,
        semantic_score: float,
        keyword_score: float,
        combined_score: float
    ):
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.document_title = document_title
        self.service = service
        self.category = category
        self.doc_type = doc_type
        self.chunk_index = chunk_index
        self.content = content
        self.semantic_score = semantic_score
        self.keyword_score = keyword_score
        self.combined_score = combined_score

class VectorStoreAdapter:
    def __init__(self, db: Session):
        self.db = db

    def search_hybrid(
        self,
        query: str,
        query_vector: List[float],
        top_k: int = 5,
        service_filter: Optional[str] = None,
        category_filter: Optional[str] = None,
        doc_type_filter: Optional[str] = None,
        min_relevance_threshold: float = 0.35
    ) -> List[ScoredChunkResult]:
        """
        Retrieves chunks using hybrid semantic cosine similarity + keyword overlap
        with metadata filtering and relevance thresholding.
        """
        # Query active indexed chunks joined with document metadata
        q = (
            self.db.query(DocumentChunk, KnowledgeDocument)
            .join(KnowledgeDocument, DocumentChunk.document_id == KnowledgeDocument.id)
            .filter(KnowledgeDocument.status == "INDEXED")
        )

        if doc_type_filter:
            q = q.filter(KnowledgeDocument.doc_type == doc_type_filter)

        # Note: If category or service filter is provided, we can either strictly filter
        # or boost matches to ensure relevant results across services
        rows = q.all()

        scored: List[ScoredChunkResult] = []

        for chunk, doc in rows:
            # Metadata soft-matching boost
            meta_boost = 1.0
            if category_filter and doc.category.lower() == category_filter.lower():
                meta_boost += 0.15
            if service_filter and (doc.service.lower() in service_filter.lower() or service_filter.lower() in doc.service.lower()):
                meta_boost += 0.20

            sem_sim = compute_cosine_similarity(query_vector, chunk.embedding_vector or [])
            kw_sim = compute_keyword_overlap(query, chunk.content)

            # Combined hybrid scoring (75% semantic, 25% keyword overlap, multiplied by metadata affinity)
            combined = round((0.75 * sem_sim + 0.25 * kw_sim) * meta_boost, 4)
            combined = min(1.0, combined)

            if combined >= min_relevance_threshold:
                scored.append(
                    ScoredChunkResult(
                        chunk_id=chunk.id,
                        document_id=doc.id,
                        document_title=doc.title,
                        service=doc.service,
                        category=doc.category,
                        doc_type=doc.doc_type,
                        chunk_index=chunk.chunk_index,
                        content=chunk.content,
                        semantic_score=round(sem_sim, 4),
                        keyword_score=round(kw_sim, 4),
                        combined_score=combined
                    )
                )

        scored.sort(key=lambda x: x.combined_score, reverse=True)
        return scored[:top_k]
