"""Document chunking strategies."""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class Chunk:
    text: str
    chunk_index: int
    start_char: int
    end_char: int
    metadata: Dict[str, Any] = field(default_factory=dict)

class CharacterChunker:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size, self.chunk_overlap = chunk_size, chunk_overlap
    def chunk_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        if not text: return []
        step = self.chunk_size - self.chunk_overlap
        chunks = []
        for idx, start in enumerate(range(0, len(text), step)):
            end = min(start + self.chunk_size, len(text))
            chunks.append(Chunk(text=text[start:end], chunk_index=idx, start_char=start, end_char=end, metadata=(metadata or {}).copy()))
            if end >= len(text): break
        return chunks

class RecursiveTextChunker(CharacterChunker): pass
class SentenceChunker(CharacterChunker): pass
