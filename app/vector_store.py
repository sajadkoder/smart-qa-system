from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
import math
from pathlib import Path
import re

from .document_processor import DocumentChunk


_TOKEN_RE = re.compile(r"[A-Za-z0-9']+")
_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "was",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
}


@dataclass(slots=True)
class SearchResult:
    chunk: DocumentChunk
    score: float


class SimpleVectorStore:
    def __init__(self, index_path: str | Path) -> None:
        self.index_path = Path(index_path)
        self._chunks: list[DocumentChunk] = []
        self._load()

    def add_chunks(self, chunks: list[DocumentChunk]) -> int:
        if not chunks:
            return 0

        existing_ids = {chunk.chunk_id for chunk in self._chunks}
        added = 0

        for chunk in chunks:
            if chunk.chunk_id in existing_ids:
                continue
            self._chunks.append(chunk)
            existing_ids.add(chunk.chunk_id)
            added += 1

        if added:
            self._save()

        return added

    def search(self, query: str, limit: int = 3) -> list[SearchResult]:
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        results: list[SearchResult] = []
        for chunk in self._chunks:
            score = self._score(query_tokens, chunk.text)
            if score > 0:
                results.append(SearchResult(chunk=chunk, score=score))

        results.sort(key=lambda item: item.score, reverse=True)
        return results[:limit]

    def count(self) -> int:
        return len(self._chunks)

    def list_sources(self) -> list[str]:
        return sorted({chunk.source for chunk in self._chunks})

    def clear(self) -> None:
        self._chunks = []
        if self.index_path.exists():
            self.index_path.unlink()

    def _load(self) -> None:
        if not self.index_path.exists():
            return

        raw_chunks = json.loads(self.index_path.read_text(encoding="utf-8"))
        self._chunks = [DocumentChunk(**raw_chunk) for raw_chunk in raw_chunks]

    def _save(self) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [chunk.to_dict() for chunk in self._chunks]
        self.index_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _score(self, query_tokens: list[str], text: str) -> float:
        text_tokens = self._tokenize(text)
        if not text_tokens:
            return 0.0

        query_counter = Counter(query_tokens)
        text_counter = Counter(text_tokens)
        overlap = query_counter & text_counter
        lexical_overlap = sum(overlap.values())
        if lexical_overlap == 0:
            return 0.0

        coverage = lexical_overlap / max(len(query_tokens), 1)
        density = lexical_overlap / math.sqrt(len(text_tokens))
        phrase_bonus = 0.5 if " ".join(query_tokens) in text.lower() else 0.0
        return round((coverage * 2.0) + density + phrase_bonus, 6)

    def _tokenize(self, text: str) -> list[str]:
        tokens = [token.lower() for token in _TOKEN_RE.findall(text)]
        filtered = [token for token in tokens if token not in _STOPWORDS]
        return filtered or tokens
