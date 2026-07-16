from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.document import Document
from app.models.document_chunk import DocumentChunkRecord
from app.models.user import User
from app.rag.chunker import DocumentChunk
from app.schemas.document import (
    DocumentChunkSearchResponse,
    DocumentChunkSearchResult,
    DocumentStatusResponse,
    DocumentUploadResponse,
)
from app.services.document_processor import DocumentProcessor
from app.services.document_vector_indexer import DocumentVectorIndexer


class DocumentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_documents(self, user: User) -> list[Document]:
        result = await self.db.execute(
            select(Document).where(Document.user_id == user.id).order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())

    async def upload_document(self, user: User, file: UploadFile) -> DocumentUploadResponse:
        filename = self._validate_pdf_filename(file.filename)
        document_id = uuid.uuid4()
        user_upload_dir = Path(settings.upload_dir) / str(user.id)
        user_upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = user_upload_dir / f"{document_id}.pdf"

        await self._save_upload(file, file_path)

        document = Document(
            id=document_id,
            user_id=user.id,
            filename=filename,
            file_path=str(file_path),
            status="pending",
            total_chunks=0,
        )
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)
        await self._process_uploaded_document(document)

        return DocumentUploadResponse(
            task_id=document.id,
            filename=document.filename,
            status=document.status,
        )

    async def get_status(self, user: User, document_id: uuid.UUID) -> DocumentStatusResponse:
        document = await self._get_user_document(user=user, document_id=document_id)
        return DocumentStatusResponse(
            task_id=document.id,
            status=document.status,
            total_chunks=document.total_chunks,
            error_message=document.error_message,
        )

    async def search_chunks(
        self,
        user: User,
        query_text: str,
        limit: int = 10,
        document_id: uuid.UUID | None = None,
    ) -> DocumentChunkSearchResponse:
        clean_query = query_text.strip()
        if not clean_query:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query cannot be empty",
            )

        like_query = f"%{clean_query}%"
        statement = (
            select(DocumentChunkRecord, Document.filename)
            .join(Document, Document.id == DocumentChunkRecord.document_id)
            .where(
                DocumentChunkRecord.user_id == user.id,
                Document.user_id == user.id,
                or_(
                    DocumentChunkRecord.text.ilike(like_query),
                    DocumentChunkRecord.path.ilike(like_query),
                    DocumentChunkRecord.section.ilike(like_query),
                ),
            )
            .order_by(Document.created_at.desc(), DocumentChunkRecord.chunk_index.asc())
            .limit(limit)
        )
        if document_id is not None:
            statement = statement.where(DocumentChunkRecord.document_id == document_id)

        rows = (await self.db.execute(statement)).all()
        results = [
            DocumentChunkSearchResult(
                id=chunk.id,
                document_id=chunk.document_id,
                filename=filename,
                chunk_index=chunk.chunk_index,
                path=chunk.path,
                section=chunk.section,
                text=chunk.text,
                page_start=chunk.page_start,
                page_end=chunk.page_end,
                contains_formula=chunk.contains_formula,
                formulas_metadata=chunk.formulas_metadata,
            )
            for chunk, filename in rows
        ]
        return DocumentChunkSearchResponse(
            query=clean_query,
            total=len(results),
            results=results,
        )

    async def delete_document(self, user: User, document_id: uuid.UUID) -> bool:
        document = await self._get_user_document(user=user, document_id=document_id)
        file_path = Path(document.file_path)

        DocumentVectorIndexer().delete_document_vectors(document)
        await self.db.delete(document)
        await self.db.commit()

        if file_path.exists() and file_path.is_file():
            file_path.unlink()
        return True

    async def _get_user_document(self, user: User, document_id: uuid.UUID) -> Document:
        result = await self.db.execute(
            select(Document).where(Document.id == document_id, Document.user_id == user.id)
        )
        document = result.scalar_one_or_none()
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        return document

    @staticmethod
    def _validate_pdf_filename(filename: str | None) -> str:
        if not filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing filename",
            )

        clean_name = Path(filename).name
        if Path(clean_name).suffix.lower() != ".pdf":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported",
            )
        return clean_name

    @staticmethod
    async def _save_upload(file: UploadFile, file_path: Path) -> None:
        total_size = 0
        with file_path.open("wb") as output:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > settings.max_upload_bytes:
                    output.close()
                    file_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="PDF file exceeds the 50MB limit",
                    )
                output.write(chunk)

    async def _process_uploaded_document(self, document: Document) -> None:
        document.status = "processing"
        document.error_message = None
        await self.db.commit()

        try:
            result = DocumentProcessor().process_pdf(document.file_path)
        except Exception as exc:
            await self._delete_document_chunks(document)
            document.status = "failed"
            document.error_message = str(exc)
            document.total_chunks = 0
        else:
            persisted_chunks = await self._replace_document_chunks(document, result.chunks)
            await DocumentVectorIndexer().index_document_chunks(document, persisted_chunks)
            document.status = "processed"
            document.error_message = None
            document.total_chunks = result.total_chunks

        await self.db.commit()
        await self.db.refresh(document)

    async def _replace_document_chunks(
        self,
        document: Document,
        chunks: list[DocumentChunk],
    ) -> list[DocumentChunkRecord]:
        await self._delete_document_chunks(document)
        records = [
            DocumentChunkRecord(
                user_id=document.user_id,
                document_id=document.id,
                chunk_index=chunk.chunk_index,
                path=chunk.path,
                section=chunk.section,
                text=chunk.text,
                page_start=chunk.page_start,
                page_end=chunk.page_end,
                contains_formula=chunk.contains_formula,
                formulas_metadata=self._serialize_formulas(chunk),
            )
            for chunk in chunks
        ]
        self.db.add_all(records)
        await self.db.flush()
        return records

    async def _delete_document_chunks(self, document: Document) -> None:
        await self.db.execute(
            delete(DocumentChunkRecord).where(
                DocumentChunkRecord.document_id == document.id,
                DocumentChunkRecord.user_id == document.user_id,
            )
        )

    @staticmethod
    def _serialize_formulas(chunk: DocumentChunk) -> list[dict[str, object]]:
        return [
            {
                "raw": formula.raw,
                "latex": formula.latex,
                "source": formula.source,
                "confidence": formula.confidence,
                "status": formula.status,
                "page_number": formula.page_number,
                "bbox": list(formula.bbox),
            }
            for formula in chunk.formulas
        ]
