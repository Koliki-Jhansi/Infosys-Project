import math
import hashlib
import re
from typing import List
import httpx
from app.core.config import settings
from app.core.logging import logger

EMBEDDING_DIM = 128

def generate_mock_embedding(text: str, dim: int = EMBEDDING_DIM) -> List[float]:
    """
    Produces a deterministic semantic dense embedding vector (dimension=128)
    based on character n-grams and token hashing, normalized to unit length.
    """
    if not text:
        return [0.0] * dim

    words = re.findall(r'\b[a-zA-Z0-9_\-]+\b', text.lower())
    vector = [0.0] * dim

    for i, word in enumerate(words):
        # Hash word into bucket indices
        h1 = int(hashlib.md5(word.encode('utf-8')).hexdigest()[:8], 16) % dim
        h2 = int(hashlib.sha256(word.encode('utf-8')).hexdigest()[:8], 16) % dim
        
        # Word frequency and position weighting
        weight = 1.0 + (1.0 / (1.0 + math.log(i + 1)))
        vector[h1] += weight
        vector[h2] += weight * 0.5

    # 3-gram feature hashes for phrase context
    for j in range(len(words) - 1):
        bigram = f"{words[j]}_{words[j+1]}"
        hb = int(hashlib.md5(bigram.encode('utf-8')).hexdigest()[:8], 16) % dim
        vector[hb] += 1.5

    # Character 3-grams for subword similarity
    clean_text = f" {text.lower()} "
    for k in range(len(clean_text) - 2):
        trigram = clean_text[k:k+3]
        ht = int(hashlib.md5(trigram.encode('utf-8')).hexdigest()[:6], 16) % dim
        vector[ht] += 0.8

    # L2 normalize vector to unit sphere
    norm = math.sqrt(sum(v * v for v in vector))
    if norm > 0:
        vector = [round(v / norm, 6) for v in vector]
    else:
        vector = [0.0] * dim

    return vector

class EmbeddingService:
    def __init__(self):
        self.mock_mode = settings.AI_MOCK_MODE or not settings.EMBEDDING_API_KEY or settings.EMBEDDING_API_KEY.startswith("mock")

    async def get_embedding(self, text: str) -> List[float]:
        if self.mock_mode:
            return generate_mock_embedding(text)
        else:
            try:
                return await self._call_external_embedding(text)
            except Exception as e:
                logger.error(f"External embedding API failed: {str(e)}. Falling back to deterministic mock embedding.")
                return generate_mock_embedding(text)

    async def _call_external_embedding(self, text: str) -> List[float]:
        headers = {
            "Authorization": f"Bearer {settings.EMBEDDING_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": settings.EMBEDDING_MODEL,
            "input": text[:8000]
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post("https://api.openai.com/v1/embeddings", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["data"][0]["embedding"]
