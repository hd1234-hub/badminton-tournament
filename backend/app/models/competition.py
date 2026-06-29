from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class Competition(Base):
    __tablename__ = "competitions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=True)  # None 表示大厅/公开比赛
    format = Column(String(50), nullable=False, default="eight_player_rotation")
    status = Column(String(20), nullable=False, default="pending")
    courts = Column(Integer, default=2)
    is_public = Column(Boolean, default=False, nullable=False)
    max_players = Column(Integer, nullable=True)
    signup_deadline = Column(DateTime, nullable=True)
    scheduled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    rounds = relationship("Round", back_populates="competition", cascade="all, delete-orphan",
                          order_by="Round.round_number")
    competition_players = relationship("CompetitionPlayer", back_populates="competition",
                                       cascade="all, delete-orphan")

    @property
    def players(self):
        return [cp.player for cp in self.competition_players] if self.competition_players else []

    @property
    def player_count(self):
        return len(self.competition_players) if self.competition_players else 0


class CompetitionPlayer(Base):
    __tablename__ = "competition_players"

    id = Column(Integer, primary_key=True)
    competition_id = Column(Integer, ForeignKey("competitions.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)

    competition = relationship("Competition", back_populates="competition_players")
    player = relationship("Player")
    __table_args__ = (UniqueConstraint("competition_id", "player_id", name="uq_competition_player"),)


class Round(Base):
    __tablename__ = "rounds"

    id = Column(Integer, primary_key=True, index=True)
    competition_id = Column(Integer, ForeignKey("competitions.id"), nullable=False)
    round_number = Column(Integer, nullable=False)

    competition = relationship("Competition", back_populates="rounds")
    matches = relationship("Match", back_populates="round", cascade="all, delete-orphan")


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    round_id = Column(Integer, ForeignKey("rounds.id"), nullable=False)
    court = Column(Integer, nullable=False)
    team_a = Column(JSON, nullable=False)
    team_b = Column(JSON, nullable=False)
    score_a = Column(Integer, nullable=True)
    score_b = Column(Integer, nullable=True)
    recorded_at = Column(DateTime, nullable=True)

    round = relationship("Round", back_populates="matches")


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(String(500), nullable=True)
    location = Column(String(200), nullable=True)
    format = Column(String(50), nullable=False, default="eight_player_rotation")
    courts = Column(Integer, default=2)
    min_players = Column(Integer, nullable=False, default=8)
    max_players = Column(Integer, nullable=False, default=8)
    start_time = Column(DateTime, nullable=False)
    signup_deadline = Column(DateTime, nullable=False)
    status = Column(String(20), nullable=False, default="open")
    competition_id = Column(Integer, ForeignKey("competitions.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    signups = relationship("ActivitySignup", back_populates="activity", cascade="all, delete-orphan",
                           order_by="ActivitySignup.signed_up_at")
    competition = relationship("Competition")


class ActivitySignup(Base):
    __tablename__ = "activity_signups"

    id = Column(Integer, primary_key=True)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    status = Column(String(20), nullable=False, default="confirmed")
    signed_up_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    activity = relationship("Activity", back_populates="signups")
    player = relationship("Player")
