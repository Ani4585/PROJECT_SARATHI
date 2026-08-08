"""Embedding drivers."""
import hashlib
from typing import List, Optional
import numpy as np

class BaseEmbeddingDriver:
    def __init__(self, dimension: int = 1536): self.dimension = dimension

class MockEmbeddingDriver(BaseEmbeddingDriver):
    def _generate_vector(self, text: str) -> List[float]:
        hash_val = hashlib.sha256(text.encode('utf-8')).hexdigest()
        rng = np.random.RandomState(int(hash_val[:8], 16))
        vec = rng.randn(self.dimension).astype(np.float32)
        norm = np.linalg.norm(vec)
        return (vec / norm).tolist() if norm > 0 else vec.tolist()

    async def embed_query(self, text: str) -> List[float]: return self._generate_vector(text)
    async def embed_documents(self, texts: List[str]) -> List[List[float]]: return [self._generate_vector(t) for t in texts]

class OpenAIEmbeddingDriver(MockEmbeddingDriver): pass
class HuggingFaceEmbeddingDriver(MockEmbeddingDriver): pass
