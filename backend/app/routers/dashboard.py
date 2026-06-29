from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.dashboard import DashboardResponse
from app.services import dashboard_service

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/clubs/{club_id}", response_model=DashboardResponse)
def get_club_dashboard(club_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return dashboard_service.get_club_dashboard(db, club_id, user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
