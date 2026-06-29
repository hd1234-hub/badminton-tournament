from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class CreateCompetitionRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    club_id: int | None = None
    format: str = "eight_player_rotation"
    courts: int = Field(default=2, ge=1, le=4)
    player_ids: list[int] = Field(default_factory=list)
    scheduled_at: datetime | None = None
    open_signup: bool = False
    is_public: bool = False
    max_players: int | None = Field(default=None, ge=2, le=64)
    signup_deadline: datetime | None = None


class ScoreRequest(BaseModel):
    score_a: int = Field(ge=0, le=30)
    score_b: int = Field(ge=0, le=30)


class MatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    round_id: int
    court: int
    team_a: list[int]
    team_b: list[int]
    score_a: int | None
    score_b: int | None


class RoundResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    competition_id: int
    round_number: int
    matches: list[MatchResponse]


class PlayerSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    level: int = 3
    gender: str = ""
    handedness: str = "right"


class CompetitionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    club_id: int | None = None
    format: str
    status: str
    courts: int
    is_public: bool = False
    max_players: int | None = None
    signup_deadline: datetime | None = None
    scheduled_at: datetime | None
    players: list[PlayerSummary]
    rounds: list[RoundResponse]


class CompetitionSummary(BaseModel):
    id: int
    name: str
    club_id: int | None = None
    format: str
    status: str
    is_public: bool = False
    max_players: int | None = None
    signup_deadline: datetime | None = None
    creator_name: str | None = None
    my_joined: bool = False
    player_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MyCompetitionSummary(BaseModel):
    id: int
    name: str
    club_id: int | None = None
    format: str
    status: str
    created_at: datetime
    scheduled_at: datetime | None = None
    my_matches: int
    my_wins: int
    my_losses: int
    my_win_rate: float
