from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.core.storage import storage_provider
from src.database.models import Document, DocumentLink, Worker
from src.schemas.document import DocumentListResponse, DocumentResponse, DocumentUpdateRequest


def get_worker_for_document(db: Session, *, organization_id: str, worker_id: str) -> Worker:
    worker = db.execute(
        select(Worker).where(Worker.organization_id == organization_id, Worker.id == worker_id)
    ).scalar_one_or_none()
    if worker is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")
    return worker


def get_document_by_id(
    db: Session,
    *,
    organization_id: str,
    document_id: str,
    required: bool = True,
) -> Document | None:
    doc = db.execute(
        select(Document)
        .options(selectinload(Document.uploaded_by_user), selectinload(Document.links))
        .where(Document.organization_id == organization_id, Document.id == document_id)
    ).scalar_one_or_none()

    if doc is None and required:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


def upload_worker_document(
    db: Session,
    *,
    organization_id: str,
    uploaded_by_user_id: str,
    worker_id: str,
    document_type: str,
    upload_file: UploadFile,
) -> Document:
    # Ensure worker exists in organization
    get_worker_for_document(db, organization_id=organization_id, worker_id=worker_id)

    normalized_doc_type = document_type.strip()
    if not normalized_doc_type:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document type is required")

    storage_path, unique_file_name, file_size, mime_type = storage_provider.save_worker_file(
        worker_id=worker_id,
        upload_file=upload_file,
    )

    doc = Document(
        organization_id=organization_id,
        uploaded_by_user_id=uploaded_by_user_id,
        file_name=unique_file_name,
        original_file_name=upload_file.filename or unique_file_name,
        mime_type=mime_type,
        storage_path=storage_path,
        file_size_bytes=file_size,
        category=normalized_doc_type,
        is_active=True,
    )

    db.add(doc)
    db.flush()

    link = DocumentLink(
        organization_id=organization_id,
        document_id=doc.id,
        worker_id=worker_id,
        tag=normalized_doc_type,
    )
    db.add(link)
    db.commit()

    # Dispatch notification to organization admins
    try:
        from src.services.notifications import notify_organization_admins
        notify_organization_admins(
            db,
            organization_id=organization_id,
            notification_type="document_uploaded",
            title="Worker Document Uploaded",
            message=f"Document '{doc.original_file_name}' ({doc.category}) was uploaded.",
            worker_id=worker_id,
        )
    except Exception as notif_err:
        print(f"Notification dispatch warning: {notif_err}")

    return get_document_by_id(db, organization_id=organization_id, document_id=doc.id, required=True)


def get_worker_documents(db: Session, *, organization_id: str, worker_id: str) -> DocumentListResponse:
    get_worker_for_document(db, organization_id=organization_id, worker_id=worker_id)

    rows = db.execute(
        select(Document, DocumentLink)
        .join(DocumentLink, DocumentLink.document_id == Document.id)
        .options(selectinload(Document.uploaded_by_user))
        .where(
            Document.organization_id == organization_id,
            DocumentLink.organization_id == organization_id,
            DocumentLink.worker_id == worker_id,
            Document.is_active == True,
        )
        .order_by(Document.created_at.desc())
    ).all()

    items = [to_document_response(doc, worker_id=worker_id) for doc, link in rows]
    return DocumentListResponse(items=items, total=len(items))


def list_documents(
    db: Session,
    *,
    organization_id: str,
    worker_id: Optional[str] = None,
    category: Optional[str] = None,
) -> DocumentListResponse:
    query = (
        select(Document, DocumentLink.worker_id)
        .outerjoin(DocumentLink, DocumentLink.document_id == Document.id)
        .options(selectinload(Document.uploaded_by_user))
        .where(Document.organization_id == organization_id, Document.is_active == True)
    )

    if worker_id:
        query = query.where(DocumentLink.worker_id == worker_id)
    if category:
        query = query.where(Document.category == category.strip())

    rows = db.execute(query.order_by(Document.created_at.desc())).all()
    items = [to_document_response(doc, worker_id=w_id) for doc, w_id in rows]
    return DocumentListResponse(items=items, total=len(items))


def get_document_file_path(db: Session, *, organization_id: str, document_id: str) -> Tuple[Path, str, str]:
    doc = get_document_by_id(db, organization_id=organization_id, document_id=document_id, required=True)
    file_path = storage_provider.get_absolute_path(doc.storage_path)

    if file_path is None or not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Physical file not found on server")

    return file_path, doc.original_file_name, doc.mime_type


def update_document_metadata(
    db: Session,
    *,
    organization_id: str,
    document_id: str,
    payload: DocumentUpdateRequest,
) -> Document:
    doc = get_document_by_id(db, organization_id=organization_id, document_id=document_id, required=True)

    if payload.document_type is not None:
        doc.category = payload.document_type.strip()
    if payload.is_active is not None:
        doc.is_active = payload.is_active

    db.add(doc)
    db.commit()
    return get_document_by_id(db, organization_id=organization_id, document_id=document_id, required=True)


def delete_document(db: Session, *, organization_id: str, document_id: str) -> None:
    doc = get_document_by_id(db, organization_id=organization_id, document_id=document_id, required=True)

    # Delete physical file from storage
    storage_provider.delete_file(doc.storage_path)

    # Delete document record (cascade deletes DocumentLink)
    db.delete(doc)
    db.commit()


def to_document_response(doc: Document, worker_id: Optional[str] = None) -> DocumentResponse:
    target_worker_id = worker_id
    if target_worker_id is None and doc.links:
        for link in doc.links:
            if link.worker_id:
                target_worker_id = link.worker_id
                break

    return DocumentResponse(
        id=doc.id,
        organization_id=doc.organization_id,
        worker_id=target_worker_id,
        document_type=doc.category,
        file_name=doc.file_name,
        original_file_name=doc.original_file_name,
        file_path=doc.storage_path,
        file_size=doc.file_size_bytes,
        mime_type=doc.mime_type,
        uploaded_by=doc.uploaded_by_user_id,
        uploaded_by_name=doc.uploaded_by_user.full_name if doc.uploaded_by_user else "System User",
        created_at=doc.created_at,
    )
