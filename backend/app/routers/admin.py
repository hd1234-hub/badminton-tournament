from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_admin_user
from app.models.user import User
from app.schemas.admin import (
    AdminCompetitionListResponse,
    AdminOverviewStats,
    AdminUserListResponse,
    RegistrationTrendItem,
)
from app.services import admin_service

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/stats", response_model=AdminOverviewStats)
def get_stats(_admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    return admin_service.get_overview_stats(db)


@router.get("/stats/registrations", response_model=list[RegistrationTrendItem])
def get_registration_trend(
    days: int = Query(default=30, ge=1, le=90),
    _admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    return admin_service.get_registration_trend(db, days)


@router.get("/users", response_model=AdminUserListResponse)
def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str = Query(default=""),
    _admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    return admin_service.list_users(db, page, page_size, search)


@router.get("/competitions/recent", response_model=AdminCompetitionListResponse)
def list_recent_competitions(
    limit: int = Query(default=10, ge=1, le=50),
    _admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    return admin_service.list_recent_competitions(db, limit)
