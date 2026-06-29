from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=100)
    name: str = Field(min_length=1, max_length=50)
    gender: str = Field(default="", max_length=10)
    skill_level: int = Field(default=0, ge=0, le=9)
    birth_year: int = Field(default=0, ge=1900, le=2100)
    bio: str = Field(default="", max_length=200)


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    name: str
    gender: str = ""
    skill_level: int = 0
    birth_year: int = 0
    bio: str = ""
    is_admin: bool = False

    @field_validator("is_admin", mode="before")
    @classmethod
    def none_to_false(cls, v: bool | None) -> bool:
        return bool(v) if v is not None else False

    @field_validator("gender", "bio", mode="before")
    @classmethod
    def none_to_empty_str(cls, v: str | None) -> str:
        return v if v is not None else ""

    @field_validator("skill_level", "birth_year", mode="before")
    @classmethod
    def none_to_zero(cls, v: int | None) -> int:
        return v if v is not None else 0


class ProfileUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    gender: str = Field(default="", max_length=10)
    skill_level: int = Field(default=0, ge=0, le=9)
    birth_year: int = Field(default=0, ge=0, le=2100)  # 0 表示未设置
    bio: str = Field(default="", max_length=200)


class AuthResponse(BaseModel):
    token: str
    user: UserResponse
