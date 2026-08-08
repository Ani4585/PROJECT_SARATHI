"""BM25Okapi lexical retriever."""
import re, math
from collections import Counter, defaultdict
from typing import List, Dict, Any, Optional
from sarathi.vector_rag.document import VectorDocument, SearchResult
from sarathi.vector_rag.filter import MetadataFilter

class BM25Retriever:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.documents, self.doc_len, self.doc_freqs, self.idf = {}, {}, {}, {}
        self.corpus_size, self.avg_doc_len = 0, 0.0

    def add_documents(self, docs: List[VectorDocument]):
        for doc in docs:
            if not doc.text: continue
            tokens = re.findall(r'\b\w+\b', doc.text.lower())
            self.documents[doc.id] = doc
            self.doc_len[doc.id] = len(tokens)
            self.doc_freqs[doc.id] = Counter(tokens)
        self.corpus_size = len(self.documents)
        if self.corpus_size > 0:
            self.avg_doc_len = sum(self.doc_len.values()) / self.corpus_size
            df = defaultdict(int)
            for freqs in self.doc_freqs.values():
                for word in freqs.keys(): df[word] += 1
            for word, freq in df.items():
                self.idf[word] = max(0.01, math.log(1.0 + (self.corpus_size - freq + 0.5) / (freq + 0.5)))

    def search(self, query: str, top_k: int = 10, filter_spec: Optional[Dict[str, Any]] = None, tenant_id: Optional[str] = None) -> List[SearchResult]:
        tokens = re.findall(r'\b\w+\b', query.lower())
        if not tokens or not self.documents: return []
        scores = defaultdict(float)
        for did, doc in self.documents.items():
            if tenant_id is not None and doc.tenant_id != tenant_id: continue
            if filter_spec and not MetadataFilter.matches(filter_spec, doc.metadata): continue
            d_len = self.doc_len[did]
            freqs = self.doc_freqs[did]
            for token in tokens:
                if token in freqs:
                    tf, idf = freqs[token], self.idf.get(token, 0.0)
                    scores[did] += idf * ((tf * (self.k1 + 1.0)) / (tf + self.k1 * (1.0 - self.b + self.b * (d_len / (self.avg_doc_len or 1.0)))))
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [SearchResult(doc_id=did, score=score, document=self.documents[did], retrieval_type="sparse") for did, score in sorted_docs[:top_k]]
