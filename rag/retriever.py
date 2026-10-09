"""
AeroAssist AI - Airport Domain Knowledge Retriever
Implements TF-IDF Vectorization and Cosine Similarity to find relevant airport support articles.
"""
import re
from typing import List, Dict, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .knowledge_base import load_knowledge_base

DEFAULT_SIMILARITY_THRESHOLD = 0.20

class AirportRetriever:
    def __init__(self, relevance_threshold: float = DEFAULT_SIMILARITY_THRESHOLD):
        self.relevance_threshold = relevance_threshold
        self.articles = []
        self.vectorizer = None
        self.kb_vectors = None
        self._build_index()

    def _build_index(self):
        """Builds TF-IDF matrix for all airport knowledge base articles with multi-field weighting."""
        self.articles = load_knowledge_base()
        
        # Combine title (3x), category/cluster (2x), keywords (3x), and content for rich lexical matching
        corpus = []
        for art in self.articles:
            title = art.get("title", "")
            cat = art.get("category", "")
            cluster = art.get("cluster", "")
            keywords_str = " ".join(art.get("keywords", []))
            content = art.get("content", "")
            doc_text = f"{title} {title} {title} {cat} {cat} {cluster} {cluster} {keywords_str} {keywords_str} {keywords_str} {content}"
            corpus.append(doc_text)

        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words="english",
            sublinear_tf=True
        )
        self.kb_vectors = self.vectorizer.fit_transform(corpus)

    def retrieve(self, query: str, top_k: int = 3) -> Dict:
        """
        Executes TF-IDF vectorization and cosine similarity against knowledge base.
        Returns:
            {
                "knowledge_found": bool,
                "top_article": dict or None,
                "similarity_score": float,
                "raw_score": float,
                "ranked_articles": list of dicts,
                "relevance_threshold": float
            }
        """
        if not query or not query.strip():
            return {
                "knowledge_found": False,
                "top_article": None,
                "similarity_score": 0.0,
                "raw_score": 0.0,
                "ranked_articles": [],
                "relevance_threshold": self.relevance_threshold
            }

        # Calculate cosine similarity
        query_vec = self.vectorizer.transform([query.strip()])
        raw_similarities = cosine_similarity(query_vec, self.kb_vectors)[0]

        ranked_indices = np.argsort(raw_similarities)[::-1]
        ranked_results = []

        for idx in ranked_indices:
            raw_score = float(raw_similarities[idx])
            article = self.articles[idx]

            # Calibrate similarity score from raw cosine to standardized 0-1 scale
            if raw_score >= self.relevance_threshold:
                calibrated_sim = min(0.96, round(0.52 + (raw_score - self.relevance_threshold) * 1.35, 4))
            else:
                calibrated_sim = round(raw_score, 4)

            ranked_results.append({
                "id": article["id"],
                "title": article["title"],
                "category": article["category"],
                "cluster": article["cluster"],
                "content": article["content"],
                "similarity_score": calibrated_sim,
                "raw_score": round(raw_score, 4)
            })

        top_match = ranked_results[0] if ranked_results else None
        top_score = top_match["similarity_score"] if top_match else 0.0
        top_raw = top_match["raw_score"] if top_match else 0.0

        knowledge_found = bool(top_raw >= self.relevance_threshold and top_score >= 0.50)

        # Filter candidate articles (default top_k, returning up to top_k matching or top results)
        filtered_articles = [art for art in ranked_results[:top_k] if art["raw_score"] >= self.relevance_threshold]

        return {
            "knowledge_found": knowledge_found,
            "top_article": top_match if knowledge_found else (top_match if top_raw > 0 else None),
            "similarity_score": top_score,
            "raw_score": top_raw,
            "ranked_articles": filtered_articles if knowledge_found else ranked_results[:top_k],
            "top_5_articles": ranked_results[:5],
            "relevance_threshold": self.relevance_threshold
        }


# Global singleton instance
_retriever_instance = None

def get_retriever(threshold: float = DEFAULT_SIMILARITY_THRESHOLD) -> AirportRetriever:
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = AirportRetriever(relevance_threshold=threshold)
    return _retriever_instance
