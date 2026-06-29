from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.activity import ActivityCreate
from app.services import activity_service

router = APIRouter(prefix="/api/v1/activities", tags=["activities"])


@router.post("")
def create(req: ActivityCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return activity_service.create_activity(db, user, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/club/{club_id}")
def list_club(club_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return activity_service.list_club_activities(db, club_id, user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{activity_id}")
def get(activity_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return activity_service.get_activity(db, activity_id, user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{activity_id}/signup")
def signup(activity_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return activity_service.signup(db, activity_id, user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{activity_id}/cancel")
def cancel(activity_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return activity_service.cancel_signup(db, activity_id, user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{activity_id}/generate")
def generate(activity_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return activity_service.generate_competition(db, activity_id, user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
