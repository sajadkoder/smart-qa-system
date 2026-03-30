from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re

from docx import Document
from pypdf import PdfReader

from .config import Settings


SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


@dataclass(slots=True)
class DocumentChunk:
    chunk_id: str
    source: str
    text: str
    position: int

    def to_dict(self) -> dict[str, str | int]:
        return asdict(self)


class DocumentProcessor:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def extract_text(self, file_path: str | Path) -> str:
        path = Path(file_path)
        extension = path.suffix.lower()

        if extension not in SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {extension or 'unknown'}")

        if extension in {".txt", ".md"}:
            text = path.read_text(encoding="utf-8")
        elif extension == ".pdf":
            text = self._read_pdf(path)
        else:
            text = self._read_docx(path)

        normalized = self._normalize_text(text)
        if not normalized:
            raise ValueError(f"No readable text found in {path.name}")

        return normalized

    def chunk_text(self, text: str, source: str) -> list[DocumentChunk]:
        cleaned_text = self._normalize_text(text)
        if not cleaned_text:
            return []

        sentences = [part.strip() for part in _SENTENCE_SPLIT_RE.split(cleaned_text) if part.strip()]
        if not sentences:
            sentences = [cleaned_text]

        chunks: list[DocumentChunk] = []
        current_sentences: list[str] = []
        current_length = 0
        max_size = self.settings.chunk_size

        for sentence in sentences:
            sentence_length = len(sentence) + (1 if current_sentences else 0)
            if current_sentences and current_length + sentence_length > max_size:
                chunks.append(self._build_chunk(current_sentences, source, len(chunks)))
                overlap_text = self._tail_overlap(" ".join(current_sentences))
                current_sentences = [overlap_text, sentence] if overlap_text else [sentence]
                current_length = len(" ".join(current_sentences))
                continue

            current_sentences.append(sentence)
            current_length += sentence_length

        if current_sentences:
            chunks.append(self._build_chunk(current_sentences, source, len(chunks)))

        return chunks

    def _build_chunk(self, sentences: list[str], source: str, position: int) -> DocumentChunk:
        text = " ".join(part.strip() for part in sentences if part.strip()).strip()
        return DocumentChunk(
            chunk_id=f"{source}:{position}",
            source=source,
            text=text,
            position=position,
        )

    def _tail_overlap(self, text: str) -> str:
        if not text or self.settings.chunk_overlap <= 0:
            return ""
        return text[-self.settings.chunk_overlap :].strip()

    def _read_pdf(self, path: Path) -> str:
        reader = PdfReader(str(path))
        pages = [(page.extract_text() or "").strip() for page in reader.pages]
        return "\n\n".join(page for page in pages if page)

    def _read_docx(self, path: Path) -> str:
        document = Document(str(path))
        paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
        return "\n\n".join(paragraphs)

    def _normalize_text(self, text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        lines = [re.sub(r"\s+", " ", line).strip() for line in text.split("\n")]
        collapsed = "\n".join(lines)
        collapsed = re.sub(r"\n{3,}", "\n\n", collapsed)
        return collapsed.strip()
