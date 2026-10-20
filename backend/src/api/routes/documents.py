from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from src.api.deps import require_roles
from src.database.models import User
from src.db.session import get_db
from src.schemas.document import DocumentListResponse, DocumentResponse, DocumentUpdateRequest
from src.services.documents import (
    delete_document,
    get_document_by_id,
    get_document_file_path,
    get_worker_documents,
    list_documents,
    to_document_response,
    update_document_metadata,
    upload_worker_document,
)

router = APIRouter()


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document_route(
    worker_id: str = Form(..., description="Target worker ID"),
    document_type: str = Form(..., description="Document category (e.g. Aadhaar, PAN, Bank Document)"),
    file: UploadFile = File(..., description="Document file (PDF, JPG, PNG up to 10MB)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> DocumentResponse:
    doc = upload_worker_document(
        db,
        organization_id=current_user.organization_id,
        uploaded_by_user_id=current_user.id,
        worker_id=worker_id,
        document_type=document_type,
        upload_file=file,
    )
    return to_document_response(doc, worker_id=worker_id)


@router.get("/", response_model=DocumentListResponse)
def list_documents_route(
    worker_id: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> DocumentListResponse:
    return list_documents(
        db,
        organization_id=current_user.organization_id,
        worker_id=worker_id,
        category=category,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document_route(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> DocumentResponse:
    doc = get_document_by_id(db, organization_id=current_user.organization_id, document_id=document_id, required=True)
    return to_document_response(doc)


@router.get("/{document_id}/file")
def download_document_file_route(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> FileResponse:
    file_path, original_file_name, mime_type = get_document_file_path(
        db,
        organization_id=current_user.organization_id,
        document_id=document_id,
    )
    return FileResponse(
        path=file_path,
        media_type=mime_type,
        filename=original_file_name,
    )


@router.patch("/{document_id}", response_model=DocumentResponse)
def update_document_route(
    document_id: str,
    payload: DocumentUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> DocumentResponse:
    doc = update_document_metadata(
        db,
        organization_id=current_user.organization_id,
        document_id=document_id,
        payload=payload,
    )
    return to_document_response(doc)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document_route(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> Response:
    delete_document(db, organization_id=current_user.organization_id, document_id=document_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Additional worker sub-router endpoint: GET /api/v1/workers/{worker_id}/documents
worker_documents_router = APIRouter()


@worker_documents_router.get("/{worker_id}/documents", response_model=DocumentListResponse)
def get_worker_documents_route(
    worker_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> DocumentListResponse:
    return get_worker_documents(db, organization_id=current_user.organization_id, worker_id=worker_id)
