from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.player import PlayerCreate, PlayerResponse
from app.services import player_service

router = APIRouter(prefix="/api/v1/players", tags=["players"])


@router.post("", response_model=PlayerResponse)
def create(req: PlayerCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return player_service.create_player(db, req.name, req.level, req.handedness, req.gender)


@router.get("", response_model=list[PlayerResponse])
def list_players(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return player_service.list_players(db)
