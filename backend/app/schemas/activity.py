from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.player import PlayerResponse


class ActivityCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    club_id: int
    format: str = "eight_player_rotation"
    courts: int = Field(default=2, ge=1, le=4)
    min_players: int = Field(default=8, ge=2)
    max_players: int = Field(default=8, ge=2)
    start_time: datetime
    signup_deadline: datetime
    location: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=500)


class ActivitySignupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    activity_id: int
    player_id: int
    status: str
    signed_up_at: datetime
    player: PlayerResponse


class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    club_id: int
    title: str
    description: str | None
    location: str | None
    format: str
    courts: int
    min_players: int
    max_players: int
    start_time: datetime
    signup_deadline: datetime
    status: str
    competition_id: int | None
    created_at: datetime
    signups: list[ActivitySignupResponse]
    confirmed_count: int
    waitlist_count: int
    my_signup_status: str | None = None
