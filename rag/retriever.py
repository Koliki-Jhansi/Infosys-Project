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
        """Builds TF-IDF matrix for all airport knowledge base articles."""
        self.articles = load_knowledge_base()
        
        # Combine title, keywords, category, and content for rich lexical matching
        corpus = []
        for art in self.articles:
            keywords_str = " ".join(art.get("keywords", []))
            doc_text = f"{art.get('title', '')} {art.get('category', '')} {art.get('cluster', '')} {keywords_str} {art.get('content', '')}"
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
                "ranked_articles": list of dicts,
                "relevance_threshold": float
            }
        """
        if not query or not query.strip():
            return {
                "knowledge_found": False,
                "top_article": None,
                "similarity_score": 0.0,
                "ranked_articles": [],
                "relevance_threshold": self.relevance_threshold
            }

        # Calculate cosine similarity
        query_vec = self.vectorizer.transform([query.strip()])
        raw_similarities = cosine_similarity(query_vec, self.kb_vectors)[0]

        ranked_indices = np.argsort(raw_similarities)[::-1]
        ranked_results = []

        # Tokenize query for keyword relevance validation
        query_tokens = set(re.findall(r"\b\w{3,}\b", query.lower()))

        for idx in ranked_indices:
            raw_score = float(raw_similarities[idx])
            article = self.articles[idx]
            
            # Boost score when title or keywords directly match query tokens
            art_keywords = set(article.get("keywords", []))
            title_tokens = set(re.findall(r"\b\w{3,}\b", article.get("title", "").lower()))
            overlap = len(query_tokens.intersection(art_keywords.union(title_tokens)))

            calibrated_score = raw_score
            if raw_score > 0.12 and overlap >= 2:
                # Calibrate to realistic 0-1 confidence scale
                calibrated_score = min(0.98, raw_score * 1.65 + (overlap * 0.05))
            elif raw_score > 0.08:
                calibrated_score = min(0.90, raw_score * 1.4)
            else:
                calibrated_score = raw_score

            ranked_results.append({
                "id": article["id"],
                "title": article["title"],
                "category": article["category"],
                "cluster": article["cluster"],
                "content": article["content"],
                "similarity_score": round(calibrated_score, 4),
                "raw_score": round(raw_score, 4)
            })

        top_match = ranked_results[0] if ranked_results else None
        top_score = top_match["similarity_score"] if top_match else 0.0

        knowledge_found = bool(top_score >= self.relevance_threshold)

        # Filter candidate articles
        filtered_articles = [art for art in ranked_results[:top_k] if art["similarity_score"] >= self.relevance_threshold]

        return {
            "knowledge_found": knowledge_found,
            "top_article": top_match if knowledge_found else (top_match if top_score > 0 else None),
            "similarity_score": top_score,
            "ranked_articles": filtered_articles if knowledge_found else ranked_results[:top_k],
            "relevance_threshold": self.relevance_threshold
        }


# Global singleton instance
_retriever_instance = None

def get_retriever(threshold: float = DEFAULT_SIMILARITY_THRESHOLD) -> AirportRetriever:
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = AirportRetriever(relevance_threshold=threshold)
    return _retriever_instance
