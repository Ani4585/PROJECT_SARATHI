"""Embedding drivers."""
import hashlib
import random
import math
from typing import List, Optional

class BaseEmbeddingDriver:
    def __init__(self, dimension: int = 1536):
        self.dimension = dimension

class MockEmbeddingDriver(BaseEmbeddingDriver):
    def _generate_vector(self, text: str) -> List[float]:
        hash_val = hashlib.sha256(text.encode('utf-8')).hexdigest()
        seed = int(hash_val[:8], 16)
        rng = random.Random(seed)
        raw_vec = [rng.gauss(0, 1) for _ in range(self.dimension)]
        norm = math.sqrt(sum(x * x for x in raw_vec))
        return [x / norm for x in raw_vec] if norm > 0 else raw_vec

    async def embed_query(self, text: str) -> List[float]:
        return self._generate_vector(text)

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._generate_vector(t) for t in texts]

class OpenAIEmbeddingDriver(MockEmbeddingDriver):
    pass

class HuggingFaceEmbeddingDriver(MockEmbeddingDriver):
    pass
