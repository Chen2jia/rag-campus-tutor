import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentStatusResponse, DocumentUploadResponse
from app.services.document_processor import DocumentProcessor


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

    async def delete_document(self, user: User, document_id: uuid.UUID) -> bool:
        document = await self._get_user_document(user=user, document_id=document_id)
        file_path = Path(document.file_path)

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
            document.status = "failed"
            document.error_message = str(exc)
            document.total_chunks = 0
        else:
            document.status = "processed"
            document.error_message = None
            document.total_chunks = result.total_chunks

        await self.db.commit()
        await self.db.refresh(document)
