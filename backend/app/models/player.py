from sqlalchemy import Column, Integer, String, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    level = Column(Integer, default=3)
    handedness = Column(String(10), default="right")
    gender = Column(String(10), default="male")

    win_rate = Column(Float, default=0.0)
    total_matches = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    point_diff = Column(Integer, default=0)


class ClubMember(Base):
    __tablename__ = "club_members"

    id = Column(Integer, primary_key=True)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    role = Column(String(20), default="member")

    club = relationship("Club", back_populates="members")
    player = relationship("Player")

    __table_args__ = (UniqueConstraint("club_id", "player_id"),)
