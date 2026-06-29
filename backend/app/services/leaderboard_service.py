from sqlalchemy.orm import Session

from app.models.player import ClubMember, Player


def get_leaderboard(db: Session, club_id: int, skip: int = 0, limit: int = 50) -> tuple[list[dict], int]:
    base_query = db.query(ClubMember.player_id).filter(ClubMember.club_id == club_id).distinct()
    total = base_query.count()
    player_ids = base_query.offset(skip).limit(limit).all()

    pids = [r[0] for r in player_ids]
    if not pids:
        return [], total

    players = db.query(Player).filter(Player.id.in_(pids)).order_by(
        Player.win_rate.desc(), Player.wins.desc()
    ).all()

    return _build_entries(players, pids), total


def get_global_leaderboard(db: Session, skip: int = 0, limit: int = 50) -> tuple[list[dict], int]:
    total = db.query(Player).count()
    players = db.query(Player).order_by(
        Player.win_rate.desc(), Player.wins.desc()
    ).offset(skip).limit(limit).all()

    pids = [p.id for p in players]
    return _build_entries(players, pids), total


def _build_entries(players, pids) -> list[dict]:
    pid_to_player = {p.id: p for p in players}
    entries = []
    for pid in pids:
        if pid not in pid_to_player:
            continue
        p = pid_to_player[pid]
        wins = p.wins or 0
        total = p.total_matches or 0
        entries.append({
            "id": p.id, "name": p.name, "level": p.level,
            "win_rate": p.win_rate or 0,
            "total_matches": total,
            "wins": wins,
            "losses": total - wins,
            "point_diff": p.point_diff or 0,
        })
    entries.sort(key=lambda e: (e["win_rate"], e["wins"], e["point_diff"]), reverse=True)
    return entries
