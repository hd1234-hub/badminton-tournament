from pydantic import BaseModel, Field


class ClubCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)


class ClubResponse(BaseModel):
    id: int
    name: str
    owner_id: int
    owner_name: str | None = None
    member_count: int = 0

    class Config:
        from_attributes = True


class ClubSearchResult(BaseModel):
    id: int
    name: str
    owner_name: str
    member_count: int
    is_joined: bool
