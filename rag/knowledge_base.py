"""
AeroAssist AI - Knowledge Base Loader
Manages the 7 clusters of airport & airways domain procedures.
"""
import os
import json
from typing import List, Dict, Optional

_KB_CACHE = None

def load_knowledge_base() -> List[Dict]:
    """Loads knowledge base articles from data/airport_knowledge_base.json."""
    global _KB_CACHE
    if _KB_CACHE is not None:
        return _KB_CACHE

    kb_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "airport_knowledge_base.json")
    if not os.path.exists(kb_path):
        raise FileNotFoundError(f"Knowledge base not found at {kb_path}")

    with open(kb_path, "r", encoding="utf-8") as f:
        _KB_CACHE = json.load(f)

    return _KB_CACHE


def get_article_by_id(kb_id: str) -> Optional[Dict]:
    """Finds article by its identifier (e.g. KB001)."""
    articles = load_knowledge_base()
    for art in articles:
        if art.get("id") == kb_id:
            return art
    return None


def get_articles_by_cluster(cluster_name: str) -> List[Dict]:
    """Returns all articles belonging to a specific cluster."""
    articles = load_knowledge_base()
    return [art for art in articles if art.get("cluster", "").upper() == cluster_name.upper()]
