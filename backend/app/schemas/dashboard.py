from datetime import datetime
from pydantic import BaseModel


class DashboardSummary(BaseModel):
    matches: int
    wins: int
    losses: int
    win_rate: float
    avg_score: float


class RecentTrendItem(BaseModel):
    match_id: int
    competition_id: int | None
    competition_name: str
    round_number: int | None
    team_score: int
    opponent_score: int
    won: bool
    recorded_at: datetime | None


class WinRatePoint(BaseModel):
    match_id: int
    recorded_at: datetime | None
    win_rate: float
    wins: int
    total: int


class OpponentRelationship(BaseModel):
    player_id: int
    player_name: str
    matches: int
    wins: int
    points_for: int
    points_against: int
    win_rate: float
    avg_point_diff: float


class PartnerMatrixItem(BaseModel):
    player_a_id: int
    player_a_name: str
    player_b_id: int
    player_b_name: str
    matches: int
    wins: int
    win_rate: float


class DashboardResponse(BaseModel):
    club_id: int
    player_id: int
    summary: DashboardSummary
    recent_trend: list[RecentTrendItem]
    win_rate_curve: list[WinRatePoint]
    opponent_relationships: list[OpponentRelationship]
    partner_matrix: list[PartnerMatrixItem]
