from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class AdminOverviewStats(BaseModel):
    total_users: int
    today_registrations: int
    week_registrations: int
    total_clubs: int
    total_competitions: int
    competitions_in_progress: int
    completed_competitions: int
    agent_messages_total: int
    agent_messages_today: int
    active_users_7d: int


class RegistrationTrendItem(BaseModel):
    date: date
    count: int


class AdminUserItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    name: str
    is_admin: bool
    created_at: datetime | None
    club_count: int = 0
    agent_messages: int = 0


class AdminUserListResponse(BaseModel):
    items: list[AdminUserItem]
    total: int
    page: int
    page_size: int


class AdminCompetitionItem(BaseModel):
    id: int
    name: str
    club_id: int | None  # 大厅比赛 club_id 为 None
    status: str
    player_count: int
    created_at: datetime | None


class AdminCompetitionListResponse(BaseModel):
    items: list[AdminCompetitionItem]
