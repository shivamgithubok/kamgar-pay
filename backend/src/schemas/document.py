from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    id: str
    organization_id: str
    worker_id: Optional[str] = None
    document_type: str = Field(..., description="Document type/category (Aadhaar, PAN, Bank Document, etc.)")
    file_name: str
    original_file_name: str
    file_path: str
    file_size: int
    mime_type: str
    uploaded_by: str
    uploaded_by_name: str
    created_at: datetime


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int


class DocumentUpdateRequest(BaseModel):
    document_type: Optional[str] = Field(default=None, max_length=50)
    is_active: Optional[bool] = Field(default=None)
