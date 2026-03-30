from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .config import Settings, get_settings
from .document_processor import SUPPORTED_EXTENSIONS
from .rag_pipeline import RAGPipeline


class IngestTextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=50_000)
    source: str = Field(default="inline.txt", min_length=1, max_length=255)


class QuestionRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1_000)


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app_settings.ensure_directories()
        app.state.settings = app_settings
        app.state.pipeline = RAGPipeline(app_settings)
        yield

    app = FastAPI(
        title=app_settings.app_name,
        version=app_settings.app_version,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    async def root() -> dict[str, object]:
        pipeline: RAGPipeline = app.state.pipeline
        return {
            "name": app_settings.app_name,
            "version": app_settings.app_version,
            "documents_indexed": len(pipeline.list_documents()),
        }

    @app.get("/health")
    async def health() -> dict[str, object]:
        pipeline: RAGPipeline = app.state.pipeline
        return {
            "status": "ok",
            "documents_indexed": len(pipeline.list_documents()),
            "chunks_indexed": pipeline.store.count(),
        }

    @app.get("/documents")
    async def list_documents() -> dict[str, object]:
        pipeline: RAGPipeline = app.state.pipeline
        return {"documents": pipeline.list_documents(), "chunks_indexed": pipeline.store.count()}

    @app.post("/documents/ingest-text")
    async def ingest_text(payload: IngestTextRequest) -> dict[str, object]:
        pipeline: RAGPipeline = app.state.pipeline
        return pipeline.ingest_text(payload.text, source=Path(payload.source).name)

    @app.post("/documents/upload")
    async def upload_document(request: Request, file: UploadFile = File(...)) -> dict[str, object]:
        pipeline: RAGPipeline = request.app.state.pipeline
        settings: Settings = request.app.state.settings

        filename = Path(file.filename or "").name
        if not filename:
            raise HTTPException(status_code=400, detail="Uploaded file must have a name.")

        extension = Path(filename).suffix.lower()
        if extension not in SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
            )

        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        max_bytes = settings.max_file_size_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"Uploaded file exceeds the {settings.max_file_size_mb} MB limit.",
            )

        destination = settings.upload_dir / filename
        destination.write_bytes(content)

        try:
            return pipeline.ingest_file(destination)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/qa/ask")
    async def ask_question(payload: QuestionRequest) -> dict[str, object]:
        pipeline: RAGPipeline = app.state.pipeline
        return pipeline.ask(payload.question)

    @app.post("/ask")
    async def ask_question_alias(payload: QuestionRequest) -> dict[str, object]:
        pipeline: RAGPipeline = app.state.pipeline
        return pipeline.ask(payload.question)

    return app


app = create_app()
