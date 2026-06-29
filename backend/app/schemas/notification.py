from datetime import datetime
from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    title: str
    message: str
    severity: str
    club_id: int | None
    activity_id: int | None
    competition_id: int | None
    match_id: int | None
    read_at: datetime | None
    created_at: datetime
