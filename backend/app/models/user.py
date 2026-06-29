from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(200), nullable=False)
    name = Column(String(50), nullable=False)
    gender = Column(String(10), default="")
    skill_level = Column(Integer, default=0)
    birth_year = Column(Integer, default=0)
    bio = Column(String(200), default="")
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    owned_clubs = relationship("Club", back_populates="owner")
