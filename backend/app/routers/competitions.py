from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.competition import (
    CompetitionResponse, CompetitionSummary, CreateCompetitionRequest, MatchResponse, MyCompetitionSummary, ScoreRequest,
)
from app.services import competition_service

router = APIRouter(prefix="/api/v1", tags=["competitions"])


@router.post("/competitions", response_model=CompetitionResponse)
def create(req: CreateCompetitionRequest, user: User = Depends(get_current_user),
           db: Session = Depends(get_db)):
    try:
        return competition_service.create_competition(
            db, req.name, req.club_id, req.format,
            req.courts, req.player_ids, req.scheduled_at,
            open_signup=req.open_signup, is_public=req.is_public, max_players=req.max_players,
            signup_deadline=req.signup_deadline,
            creator_user_id=user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/competitions/open", response_model=list[CompetitionSummary])
def list_open(
    q: str = Query(default=""),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return competition_service.list_open_competitions(db, user.id, q)


@router.get("/competitions/me", response_model=list[MyCompetitionSummary])
def list_my_competitions(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return competition_service.list_my_competitions(db, user.id)


@router.post("/competitions/{comp_id}/join", response_model=CompetitionResponse)
def join_open_competition(
    comp_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return competition_service.join_open_competition(db, comp_id, user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/competitions/{comp_id}/join", response_model=CompetitionResponse)
def leave_open_competition(
    comp_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return competition_service.leave_open_competition(db, comp_id, user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/competitions/{comp_id}", response_model=CompetitionResponse)
def get(comp_id: int, user: User = Depends(get_current_user),
        db: Session = Depends(get_db)):
    try:
        return competition_service.get_competition(db, comp_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/competitions/{comp_id}/start", response_model=CompetitionResponse)
def start(comp_id: int, user: User = Depends(get_current_user),
          db: Session = Depends(get_db)):
    try:
        return competition_service.start_competition(db, comp_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/matches/{match_id}/score", response_model=MatchResponse)
def record_score(match_id: int, req: ScoreRequest,
                 user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    try:
        return competition_service.record_score(db, match_id, req.score_a, req.score_b, user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/competitions/{comp_id}/finish", response_model=CompetitionResponse)
def finish(comp_id: int, user: User = Depends(get_current_user),
           db: Session = Depends(get_db)):
    try:
        return competition_service.finish_competition(db, comp_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
