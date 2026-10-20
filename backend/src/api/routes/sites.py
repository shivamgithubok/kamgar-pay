from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from src.api.deps import require_roles
from src.database.models import User
from src.db.session import get_db
from src.schemas.site import (
    SiteAssignmentResponse,
    SiteCreateRequest,
    SiteExpenseSummaryResponse,
    SiteListResponse,
    SiteResponse,
    SiteStatsResponse,
    SiteUpdateRequest,
    SiteWorkerAssignmentRequest,
    SiteWorkerResponse,
)
from src.services.sites import (
    assign_worker_to_site,
    create_site,
    delete_site,
    get_site_by_id,
    get_site_expense_summary,
    get_site_stats,
    list_site_workers,
    list_sites,
    to_assignment_response,
    to_site_response,
    update_site,
    unassign_worker_from_site,
)


router = APIRouter()


@router.post("", response_model=SiteResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=SiteResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_site_route(
    payload: SiteCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> SiteResponse:
    site = create_site(db, organization_id=current_user.organization_id, payload=payload)
    return to_site_response(site)


@router.get("", response_model=SiteListResponse)
@router.get("/", response_model=SiteListResponse, include_in_schema=False)
def list_sites_route(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = Query(default=None, max_length=100),
    status_filter: Optional[str] = Query(default=None, alias="status", max_length=20),
    city: Optional[str] = Query(default=None, max_length=100),
    state: Optional[str] = Query(default=None, max_length=100),
    site_manager_user_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> SiteListResponse:
    return list_sites(
        db,
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        search=search,
        status_filter=status_filter,
        city=city,
        state=state,
        site_manager_user_id=site_manager_user_id,
    )


@router.get("/{site_id}", response_model=SiteResponse)
def get_site_route(
    site_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> SiteResponse:
    site = get_site_by_id(db, organization_id=current_user.organization_id, site_id=site_id, required=True)
    return to_site_response(site)


@router.put("/{site_id}", response_model=SiteResponse)
@router.patch("/{site_id}", response_model=SiteResponse)
def update_site_route(
    site_id: str,
    payload: SiteUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> SiteResponse:
    site = update_site(db, organization_id=current_user.organization_id, site_id=site_id, payload=payload)
    return to_site_response(site)


@router.delete("/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_site_route(
    site_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin")),
) -> Response:
    delete_site(db, organization_id=current_user.organization_id, site_id=site_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{site_id}/workers", response_model=list[SiteWorkerResponse])
def list_site_workers_route(
    site_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> list[SiteWorkerResponse]:
    return list_site_workers(db, organization_id=current_user.organization_id, site_id=site_id)


@router.post("/{site_id}/workers/assign", response_model=SiteAssignmentResponse, status_code=status.HTTP_201_CREATED)
def assign_worker_to_site_route(
    site_id: str,
    payload: SiteWorkerAssignmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> SiteAssignmentResponse:
    assignment = assign_worker_to_site(
        db,
        organization_id=current_user.organization_id,
        site_id=site_id,
        payload=payload,
    )
    return to_assignment_response(assignment)


@router.delete("/{site_id}/workers/{worker_id}", status_code=status.HTTP_204_NO_CONTENT)
def unassign_worker_from_site_route(
    site_id: str,
    worker_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> Response:
    unassign_worker_from_site(
        db,
        organization_id=current_user.organization_id,
        site_id=site_id,
        worker_id=worker_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{site_id}/stats", response_model=SiteStatsResponse)
def get_site_stats_route(
    site_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> SiteStatsResponse:
    return get_site_stats(db, organization_id=current_user.organization_id, site_id=site_id)


@router.get("/{site_id}/expense-summary", response_model=SiteExpenseSummaryResponse)
def get_site_expense_summary_route(
    site_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("organization_admin", "staff")),
) -> SiteExpenseSummaryResponse:
    return get_site_expense_summary(db, organization_id=current_user.organization_id, site_id=site_id)
