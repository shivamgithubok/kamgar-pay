from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from src.api.deps import require_roles
from src.database.models import User
from src.db.session import get_db
from src.schemas.worker import WorkerCreateRequest, WorkerListResponse, WorkerResponse, WorkerUpdateRequest
from src.services.workers import (
    create_worker,
    delete_worker,
    get_advance_summaries,
    get_worker_by_id,
    list_workers,
    to_worker_response,
    update_worker,
)


router = APIRouter()


@router.post("", response_model=WorkerResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=WorkerResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_worker_route(
    payload: WorkerCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> WorkerResponse:
    worker = create_worker(db, organization_id=current_user.organization_id, payload=payload)
    return to_worker_response(worker)


@router.get("", response_model=WorkerListResponse)
@router.get("/", response_model=WorkerListResponse, include_in_schema=False)
def list_workers_route(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = Query(default=None, max_length=100),
    trade: Optional[str] = Query(default=None, max_length=80),
    status_filter: Optional[str] = Query(default=None, alias="status", max_length=20),
    site_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> WorkerListResponse:
    return list_workers(
        db,
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        search=search,
        trade=trade,
        status_filter=status_filter,
        site_id=site_id,
    )


@router.get("/{worker_id}", response_model=WorkerResponse)
def get_worker_route(
    worker_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> WorkerResponse:
    worker = get_worker_by_id(db, organization_id=current_user.organization_id, worker_id=worker_id, required=True)
    summary = get_advance_summaries(
        db,
        organization_id=current_user.organization_id,
        worker_ids=[worker.id],
    ).get(worker.id)
    return to_worker_response(worker, summary)


@router.put("/{worker_id}", response_model=WorkerResponse)
@router.patch("/{worker_id}", response_model=WorkerResponse)
def update_worker_route(
    worker_id: str,
    payload: WorkerUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> WorkerResponse:
    worker = update_worker(
        db,
        organization_id=current_user.organization_id,
        worker_id=worker_id,
        payload=payload,
    )
    summary = get_advance_summaries(
        db,
        organization_id=current_user.organization_id,
        worker_ids=[worker.id],
    ).get(worker.id)
    return to_worker_response(worker, summary)


@router.delete("/{worker_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_worker_route(
    worker_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin")),
) -> Response:
    delete_worker(db, organization_id=current_user.organization_id, worker_id=worker_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
