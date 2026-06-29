from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.club import Club
from app.models.competition import Competition
from app.models.player import ClubMember, Player
from app.models.user import User
from app.database import sync_player_id_sequence


def _ensure_player(db: Session, user: User) -> Player:
    player = db.query(Player).filter(Player.id == user.id).first()
    if not player:
        player = Player(id=user.id, name=user.name, gender=user.gender or "male")
        db.add(player)
        db.flush()
        sync_player_id_sequence()
    else:
        if player.name != user.name:
            player.name = user.name
        if user.gender and player.gender != user.gender:
            player.gender = user.gender
    return player


def create_club(db: Session, user: User, name: str) -> Club:
    existing = db.query(Club).filter(Club.name == name).first()
    if existing:
        raise ValueError("俱乐部名称已存在")
    club = Club(name=name, owner_id=user.id)
    db.add(club)
    db.flush()
    # auto-join creator as member
    player = _ensure_player(db, user)
    db.add(ClubMember(club_id=club.id, player_id=player.id, role="owner"))
    db.commit()
    db.refresh(club)
    return club


def list_user_clubs(db: Session, user: User) -> list[Club]:
    owned = db.query(Club).filter(Club.owner_id == user.id).all()
    owned_ids = [c.id for c in owned]
    member_query = db.query(ClubMember.club_id).filter(ClubMember.player_id == user.id)
    if owned_ids:
        member_query = member_query.filter(ClubMember.club_id.notin_(owned_ids))
    joined_ids = member_query.distinct().all()
    joined = db.query(Club).filter(Club.id.in_([r[0] for r in joined_ids])).all() if joined_ids else []
    return owned + joined


def search_clubs(db: Session, q: str, user_id: int) -> list[dict]:
    query = db.query(Club).filter(Club.name.contains(q))
    clubs = query.all()

    user_club_ids = set()
    user_club_ids.update(row[0] for row in db.query(ClubMember.club_id).filter(ClubMember.player_id == user_id).all())

    results = []
    for club in clubs:
        member_count = db.query(func.count(ClubMember.id)).filter(ClubMember.club_id == club.id).scalar() or 0
        results.append({
            "id": club.id,
            "name": club.name,
            "owner_name": club.owner.name,
            "member_count": member_count,
            "is_joined": club.id in user_club_ids,
        })
    return results


def get_club_competitions(db: Session, club_id: int) -> list[Competition]:
    return (
        db.query(Competition)
        .filter(Competition.club_id == club_id)
        .order_by(Competition.created_at.desc())
        .all()
    )


def join_club(db: Session, club_id: int, user: User) -> ClubMember:
    _ensure_player(db, user)
    existing = db.query(ClubMember).filter(
        ClubMember.club_id == club_id, ClubMember.player_id == user.id
    ).first()
    if existing:
        raise ValueError("你已加入该俱乐部")
    member = ClubMember(club_id=club_id, player_id=user.id, role="member")
    db.add(member)
    db.commit()
    return member


def get_club_players(db: Session, club_id: int) -> list[Player]:
    return db.query(Player).join(ClubMember).filter(ClubMember.club_id == club_id).all()


def add_player_to_club(db: Session, club_id: int, player_id: int) -> ClubMember:
    existing = db.query(ClubMember).filter(
        ClubMember.club_id == club_id, ClubMember.player_id == player_id
    ).first()
    if existing:
        raise ValueError("该球员已在此俱乐部中")
    member = ClubMember(club_id=club_id, player_id=player_id, role="member")
    db.add(member)
    db.commit()
    return member
