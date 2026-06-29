from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.services import leaderboard_service

router = APIRouter(prefix="/api/v1", tags=["leaderboard"])


@router.get("/leaderboard")
def get_leaderboard(club_id: int = Query(...), skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                    user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    entries, total = leaderboard_service.get_leaderboard(db, club_id, skip=skip, limit=limit)
    return {"entries": entries, "total": total, "skip": skip, "limit": limit}


@router.get("/leaderboard/global")
def get_global_leaderboard(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                           user: User = Depends(get_current_user),
                           db: Session = Depends(get_db)):
    entries, total = leaderboard_service.get_global_leaderboard(db, skip=skip, limit=limit)
    return {"entries": entries, "total": total, "skip": skip, "limit": limit}
