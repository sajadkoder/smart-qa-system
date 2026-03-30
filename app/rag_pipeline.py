from __future__ import annotations

from pathlib import Path
import re

from .config import Settings
from .document_processor import DocumentProcessor
from .vector_store import SearchResult, SimpleVectorStore


_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_TOKEN_RE = re.compile(r"[A-Za-z0-9']+")


class RAGPipeline:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.processor = DocumentProcessor(settings)
        self.store = SimpleVectorStore(settings.document_dir / "index.json")

    def ingest_file(self, file_path: str | Path) -> dict[str, int | str]:
        path = Path(file_path)
        text = self.processor.extract_text(path)
        chunks = self.processor.chunk_text(text, source=path.name)
        added = self.store.add_chunks(chunks)
        return {
            "source": path.name,
            "chunks_added": added,
            "stored_chunks": self.store.count(),
        }

    def ingest_text(self, text: str, source: str = "inline.txt") -> dict[str, int | str]:
        chunks = self.processor.chunk_text(text, source=source)
        added = self.store.add_chunks(chunks)
        return {
            "source": source,
            "chunks_added": added,
            "stored_chunks": self.store.count(),
        }

    def list_documents(self) -> list[str]:
        return self.store.list_sources()

    def ask(self, question: str) -> dict[str, object]:
        if self.store.count() == 0:
            return {
                "question": question,
                "answer": "No documents have been indexed yet. Upload a file or ingest text first.",
                "sources": [],
                "matches": [],
            }

        results = self.store.search(question, limit=self.settings.top_k)
        if not results:
            return {
                "question": question,
                "answer": "I couldn't find a relevant answer in the indexed documents.",
                "sources": [],
                "matches": [],
            }

        answer = self._compose_answer(question, results)
        unique_sources: list[dict[str, object]] = []
        seen_sources: set[str] = set()

        for result in results:
            if result.chunk.source in seen_sources:
                continue
            unique_sources.append(
                {
                    "source": result.chunk.source,
                    "chunk_id": result.chunk.chunk_id,
                    "score": round(result.score, 3),
                }
            )
            seen_sources.add(result.chunk.source)

        matches = [
            {
                "source": result.chunk.source,
                "score": round(result.score, 3),
                "text": self._excerpt(result.chunk.text),
            }
            for result in results
        ]

        return {
            "question": question,
            "answer": answer,
            "sources": unique_sources,
            "matches": matches,
        }

    def _compose_answer(self, question: str, results: list[SearchResult]) -> str:
        candidate_sentences: list[tuple[float, str]] = []
        question_tokens = set(self._tokenize(question))

        for result in results:
            sentences = [
                sentence.strip()
                for sentence in _SENTENCE_SPLIT_RE.split(result.chunk.text)
                if sentence.strip()
            ]
            for sentence in sentences:
                sentence_tokens = set(self._tokenize(sentence))
                overlap = len(question_tokens & sentence_tokens)
                if overlap:
                    score = (overlap * 2.0) + result.score
                    candidate_sentences.append((score, sentence))

        if candidate_sentences:
            candidate_sentences.sort(key=lambda item: item[0], reverse=True)
            selected: list[str] = []
            seen_sentences: set[str] = set()
            for _, sentence in candidate_sentences:
                if sentence in seen_sentences:
                    continue
                selected.append(sentence)
                seen_sentences.add(sentence)
                if len(selected) == 2:
                    break
            return " ".join(selected)

        return self._excerpt(results[0].chunk.text, limit=320)

    def _excerpt(self, text: str, limit: int = 220) -> str:
        if len(text) <= limit:
            return text
        return text[: limit - 3].rstrip() + "..."

    def _tokenize(self, text: str) -> list[str]:
        return [token.lower() for token in _TOKEN_RE.findall(text)]
