from pydantic import BaseModel, Field


class PlayerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    level: int = Field(default=3, ge=1, le=5)
    handedness: str = Field(default="right")
    gender: str = Field(default="male")


class PlayerResponse(BaseModel):
    id: int
    name: str
    level: int
    handedness: str
    gender: str
    win_rate: float
    total_matches: int
    wins: int

    class Config:
        from_attributes = True
