#!/usr/bin/env python3
"""Pure-standard-library hybrid retrieval with TF-IDF scoring."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Iterable


_TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?")


class HybridRetriever:
    """Deterministic TF-IDF retriever without external ML dependencies."""

    def __init__(self) -> None:
        self.documents: list[str] = []
        self.doc_vectors: list[dict[str, float]] = []
        self.idf: dict[str, float] = {}

    def _tokenize(self, text: str) -> list[str]:
        if text is None:
            return []
        return [token.lower() for token in _TOKEN_RE.findall(str(text))]

    def fit(self, documents: list[str]) -> "HybridRetriever":
        """Build an IDF model and vectorized document representations."""
        self.documents = [str(document or "") for document in documents]
        self.doc_vectors = []
        self.idf = {}

        if not self.documents:
            return self

        tokenized = [self._tokenize(document) for document in self.documents]
        document_count = len(tokenized)
        doc_frequency: Counter[str] = Counter()
        for tokens in tokenized:
            if not tokens:
                continue
            doc_frequency.update(set(tokens))

        vocabulary = sorted(doc_frequency)
        self.idf = {
            term: math.log((1.0 + document_count) / (1.0 + doc_frequency[term])) + 1.0
            for term in vocabulary
        }

        for tokens in tokenized:
            if not tokens:
                self.doc_vectors.append({})
                continue
            counts = Counter(tokens)
            token_count = max(len(tokens), 1)
            vector: dict[str, float] = {}
            for term in vocabulary:
                tf = counts.get(term, 0) / token_count
                vector[term] = tf * self.idf.get(term, 1.0)
            self.doc_vectors.append(vector)

        return self

    def _cosine_similarity(self, left: dict[str, float], right: dict[str, float]) -> float:
        if not left or not right:
            return 0.0

        common_terms = set(left) & set(right)
        if not common_terms:
            return 0.0

        dot_product = sum(left[term] * right[term] for term in common_terms)
        left_norm = math.sqrt(sum(value * value for value in left.values()))
        right_norm = math.sqrt(sum(value * value for value in right.values()))
        if left_norm == 0.0 or right_norm == 0.0:
            return 0.0
        return dot_product / (left_norm * right_norm)

    def query(self, text: str, top_k: int = 5) -> list[int]:
        """Return indices of documents ranked by TF-IDF cosine similarity."""
        if not self.documents:
            return []
        if text is None or not str(text).strip():
            return []

        query_tokens = self._tokenize(text)
        if not query_tokens:
            return []

        query_counts = Counter(query_tokens)
        query_length = max(len(query_tokens), 1)
        query_vector: dict[str, float] = {}
        for term, value in self.idf.items():
            if term in query_counts:
                query_vector[term] = (query_counts[term] / query_length) * value

        if not query_vector:
            return []

        scores: list[tuple[int, float]] = []
        for index, document_vector in enumerate(self.doc_vectors):
            scores.append((index, self._cosine_similarity(query_vector, document_vector)))

        ranked = sorted(scores, key=lambda item: (-item[1], item[0]))
        limit = max(0, min(int(top_k), len(ranked)))
        return [index for index, _ in ranked[:limit]]


def _normalize_documents(documents: Iterable[str]) -> list[str]:
    return [str(document or "") for document in documents]


if __name__ == "__main__":
    demo_documents = [
        "The project uses Python and streamlit for the developer dashboard.",
        "Supply chain hardening and secure retrieval keep tools resilient.",
        "The command center logs activity and emits governance reports.",
        "Authentication and secure retrieval require careful input validation.",
        "The architecture preserves protected directories while monitoring the project.",
    ]
    retriever = HybridRetriever().fit(demo_documents)
    print(retriever.query("secure retrieval hardening", top_k=3))
