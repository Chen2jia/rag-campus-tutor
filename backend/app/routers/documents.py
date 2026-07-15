from uuid import UUID

from fastapi import APIRouter, File, UploadFile

from app.core.deps import CurrentUser, DbSession
from app.schemas.document import (
    DeleteResponse,
    DocumentRead,
    DocumentStatusResponse,
    DocumentUploadResponse,
)
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentRead])
async def list_documents(current_user: CurrentUser, db: DbSession) -> list[DocumentRead]:
    return await DocumentService(db).list_documents(current_user)


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    current_user: CurrentUser,
    db: DbSession,
    file: UploadFile = File(...),
) -> DocumentUploadResponse:
    return await DocumentService(db).upload_document(current_user, file)


@router.get("/{task_id}/status", response_model=DocumentStatusResponse)
async def document_status(
    task_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> DocumentStatusResponse:
    return await DocumentService(db).get_status(current_user, task_id)


@router.delete("/{document_id}", response_model=DeleteResponse)
async def delete_document(
    document_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> DeleteResponse:
    success = await DocumentService(db).delete_document(current_user, document_id)
    return DeleteResponse(success=success)
