from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.club import ClubCreate, ClubResponse, ClubSearchResult
from app.schemas.competition import CompetitionSummary
from app.schemas.player import PlayerResponse
from app.services import club_service

router = APIRouter(prefix="/api/v1/clubs", tags=["clubs"])


@router.post("", response_model=ClubResponse)
def create(req: ClubCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return club_service.create_club(db, user, req.name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[ClubResponse])
def list_clubs(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    clubs = club_service.list_user_clubs(db, user)
    return [
        {
            "id": c.id,
            "name": c.name,
            "owner_id": c.owner_id,
            "owner_name": c.owner.name,
            "member_count": len(c.members),
        }
        for c in clubs
    ]


@router.get("/search", response_model=list[ClubSearchResult])
def search_clubs(q: str = Query(default=""), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return club_service.search_clubs(db, q, user.id)


@router.post("/{club_id}/join")
def join(club_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        club_service.join_club(db, club_id, user)
        return {"message": "已加入俱乐部"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{club_id}/players", response_model=list[PlayerResponse])
def get_players(club_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return club_service.get_club_players(db, club_id)


@router.get("/{club_id}/competitions", response_model=list[CompetitionSummary])
def get_competitions(club_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return club_service.get_club_competitions(db, club_id)


@router.post("/{club_id}/players/{player_id}")
def add_player(club_id: int, player_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        club_service.add_player_to_club(db, club_id, player_id)
        return {"message": "已添加球员"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
