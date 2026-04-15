"""
Algorithm 96: Indexing

- Data → index builder
- Fast inverted index
- Stored in ElasticSearch
- Query optimized
- Ranking applied
"""

import math
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class Document:
    """A document to be indexed."""
    doc_id: str
    content: str
    metadata: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class SearchResult:
    """A search result with relevance score."""
    doc_id: str
    score: float
    snippet: str = ""
    metadata: dict = field(default_factory=dict)


class Tokenizer:
    """Text tokenizer for index building."""

    STOP_WORDS = frozenset({
        "a", "an", "the", "is", "at", "which", "on", "in", "to", "for",
        "of", "and", "or", "but", "not", "with", "by", "from", "as",
        "it", "this", "that", "are", "was", "were", "be", "been",
    })

    @classmethod
    def tokenize(cls, text):
        """Tokenize text into normalized terms."""
        text = text.lower()
        tokens = re.findall(r'\b[a-z0-9]+\b', text)
        return [t for t in tokens if t not in cls.STOP_WORDS and len(t) > 1]


class InvertedIndex:
    """Fast inverted index for full-text search."""

    def __init__(self):
        self.index = defaultdict(dict)  # term -> {doc_id: [positions]}
        self.doc_lengths = {}  # doc_id -> length
        self.doc_count = 0
        self.avg_doc_length = 0
        self.documents = {}  # doc_id -> Document
        self.tokenizer = Tokenizer()

    def add_document(self, document):
        """Index a document."""
        tokens = self.tokenizer.tokenize(document.content)
        self.documents[document.doc_id] = document
        self.doc_lengths[document.doc_id] = len(tokens)

        for pos, token in enumerate(tokens):
            if document.doc_id not in self.index[token]:
                self.index[token][document.doc_id] = []
            self.index[token][document.doc_id].append(pos)

        self.doc_count += 1
        self.avg_doc_length = (
            sum(self.doc_lengths.values()) / self.doc_count
        )

    def remove_document(self, doc_id):
        """Remove a document from the index."""
        if doc_id not in self.documents:
            return

        for term in list(self.index.keys()):
            self.index[term].pop(doc_id, None)
            if not self.index[term]:
                del self.index[term]

        del self.documents[doc_id]
        del self.doc_lengths[doc_id]
        self.doc_count -= 1
        if self.doc_count > 0:
            self.avg_doc_length = sum(self.doc_lengths.values()) / self.doc_count

    def search(self, query, top_k=10):
        """Search the index using BM25 ranking."""
        query_tokens = self.tokenizer.tokenize(query)
        if not query_tokens:
            return []

        scores = defaultdict(float)

        for token in query_tokens:
            if token not in self.index:
                continue

            postings = self.index[token]
            idf = self._idf(len(postings))

            for doc_id, positions in postings.items():
                tf = len(positions)
                doc_length = self.doc_lengths.get(doc_id, 1)
                bm25_score = self._bm25_tf(tf, doc_length) * idf
                scores[doc_id] += bm25_score

        results = []
        for doc_id, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]:
            doc = self.documents.get(doc_id)
            snippet = self._generate_snippet(doc, query_tokens) if doc else ""
            results.append(SearchResult(
                doc_id=doc_id,
                score=score,
                snippet=snippet,
                metadata=doc.metadata if doc else {},
            ))

        return results

    def _idf(self, doc_freq):
        """Inverse document frequency."""
        return math.log(1 + (self.doc_count - doc_freq + 0.5) / (doc_freq + 0.5))

    def _bm25_tf(self, tf, doc_length, k1=1.2, b=0.75):
        """BM25 term frequency normalization."""
        numerator = tf * (k1 + 1)
        denominator = tf + k1 * (1 - b + b * doc_length / max(self.avg_doc_length, 1))
        return numerator / denominator

    def _generate_snippet(self, doc, query_tokens, max_length=200):
        """Generate a relevant snippet from the document."""
        content = doc.content
        best_pos = 0
        best_score = 0

        words = content.lower().split()
        for i in range(len(words)):
            window = words[i:i+20]
            score = sum(1 for w in window if w.strip(".,!?") in query_tokens)
            if score > best_score:
                best_score = score
                best_pos = i

        snippet_words = content.split()[best_pos:best_pos+30]
        snippet = " ".join(snippet_words)
        if len(snippet) > max_length:
            snippet = snippet[:max_length] + "..."
        return snippet


class SearchEngine:
    """Search engine with indexing, querying, and ranking."""

    def __init__(self):
        self.index = InvertedIndex()
        self.query_log = []

    def index_document(self, doc_id, content, metadata=None):
        """Index a document."""
        doc = Document(doc_id=doc_id, content=content, metadata=metadata or {})
        self.index.add_document(doc)

    def index_batch(self, documents):
        """Index a batch of documents."""
        for doc in documents:
            self.index.add_document(doc)

    def search(self, query, top_k=10):
        """Search indexed documents."""
        start = time.time()
        results = self.index.search(query, top_k)
        elapsed = time.time() - start

        self.query_log.append({
            "query": query,
            "results": len(results),
            "elapsed_ms": elapsed * 1000,
        })

        return results

    def get_stats(self):
        """Get search engine statistics."""
        return {
            "documents": self.index.doc_count,
            "terms": len(self.index.index),
            "queries_served": len(self.query_log),
            "avg_query_time_ms": (
                sum(q["elapsed_ms"] for q in self.query_log) / len(self.query_log)
                if self.query_log else 0
            ),
        }


if __name__ == "__main__":
    engine = SearchEngine()

    documents = [
        ("d1", "Python is a great programming language for data science", {"type": "article"}),
        ("d2", "Machine learning algorithms are used in data analysis", {"type": "article"}),
        ("d3", "JavaScript is popular for web development", {"type": "tutorial"}),
        ("d4", "Data structures and algorithms are fundamental to programming", {"type": "course"}),
        ("d5", "Python machine learning with scikit-learn library", {"type": "tutorial"}),
    ]

    for doc_id, content, meta in documents:
        engine.index_document(doc_id, content, meta)

    print(f"Indexed {engine.get_stats()['documents']} documents, "
          f"{engine.get_stats()['terms']} terms\n")

    queries = ["Python programming", "machine learning data", "web development"]
    for query in queries:
        results = engine.search(query, top_k=3)
        print(f"Query: '{query}' → {len(results)} results")
        for r in results:
            print(f"  [{r.score:.3f}] {r.doc_id}: {r.snippet[:80]}")
        print()
