from sqlalchemy.orm import Session

from app.models.player import Player
from app.database import sync_player_id_sequence


def create_player(db: Session, name: str, level: int, handedness: str, gender: str) -> Player:
    sync_player_id_sequence()
    player = Player(name=name, level=level, handedness=handedness, gender=gender)
    db.add(player)
    db.commit()
    db.refresh(player)
    return player


def list_players(db: Session) -> list[Player]:
    return db.query(Player).all()
