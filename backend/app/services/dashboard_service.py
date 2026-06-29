from collections import defaultdict

from sqlalchemy.orm import Session, joinedload

from app.models.competition import Competition, Match, Round
from app.models.player import ClubMember, Player
from app.models.user import User


def _ensure_member(db: Session, club_id: int, user: User):
    member = db.query(ClubMember).filter(
        ClubMember.club_id == club_id,
        ClubMember.player_id == user.id,
    ).first()
    if not member:
        raise ValueError("你不在该俱乐部中")


def _scored_matches(db: Session, club_id: int) -> list[Match]:
    return db.query(Match).options(joinedload(Match.round).joinedload(Round.competition)).join(Round).join(Competition).filter(
        Competition.club_id == club_id,
        Match.score_a.isnot(None),
        Match.score_b.isnot(None),
    ).order_by(Match.recorded_at.asc(), Match.id.asc()).all()


def _player_name_map(db: Session, club_id: int) -> dict[int, str]:
    players = db.query(Player).join(ClubMember).filter(ClubMember.club_id == club_id).all()
    return {p.id: p.name for p in players}


def _match_side(match: Match, player_id: int):
    if player_id in (match.team_a or []):
        return match.team_a, match.team_b, match.score_a, match.score_b
    if player_id in (match.team_b or []):
        return match.team_b, match.team_a, match.score_b, match.score_a
    return None


def get_club_dashboard(db: Session, club_id: int, user: User) -> dict:
    _ensure_member(db, club_id, user)
    player_id = user.id
    names = _player_name_map(db, club_id)
    matches = _scored_matches(db, club_id)
    my_matches = [m for m in matches if player_id in (m.team_a or []) + (m.team_b or [])]

    recent_trend = []
    total = 0
    wins = 0
    win_rate_curve = []
    opponent_stats: dict[int, dict] = {}

    for match in my_matches:
        side = _match_side(match, player_id)
        if not side:
            continue
        team, opponents, team_score, opponent_score = side
        won = team_score > opponent_score
        total += 1
        if won:
            wins += 1
        comp = match.round.competition if match.round else None
        item = {
            "match_id": match.id,
            "competition_id": comp.id if comp else None,
            "competition_name": comp.name if comp else "",
            "round_number": match.round.round_number if match.round else None,
            "team_score": team_score,
            "opponent_score": opponent_score,
            "won": won,
            "recorded_at": match.recorded_at,
        }
        recent_trend.append(item)
        win_rate_curve.append({
            "match_id": match.id,
            "recorded_at": match.recorded_at,
            "win_rate": wins / total if total else 0,
            "wins": wins,
            "total": total,
        })
        for opponent_id in opponents:
            entry = opponent_stats.setdefault(opponent_id, {
                "player_id": opponent_id,
                "player_name": names.get(opponent_id, f"球员{opponent_id}"),
                "matches": 0,
                "wins": 0,
                "points_for": 0,
                "points_against": 0,
            })
            entry["matches"] += 1
            entry["points_for"] += team_score
            entry["points_against"] += opponent_score
            if won:
                entry["wins"] += 1

    partner_stats: dict[tuple[int, int], dict] = defaultdict(lambda: {"matches": 0, "wins": 0})
    for match in matches:
        teams = [
            (match.team_a or [], match.score_a, match.score_b),
            (match.team_b or [], match.score_b, match.score_a),
        ]
        for team, team_score, opponent_score in teams:
            if len(team) < 2:
                continue
            won = team_score > opponent_score
            for i, first in enumerate(team):
                for second in team[i + 1:]:
                    key = tuple(sorted((first, second)))
                    partner_stats[key]["matches"] += 1
                    if won:
                        partner_stats[key]["wins"] += 1

    partner_matrix = []
    for (player_a_id, player_b_id), stats in partner_stats.items():
        total_matches = stats["matches"]
        partner_matrix.append({
            "player_a_id": player_a_id,
            "player_a_name": names.get(player_a_id, f"球员{player_a_id}"),
            "player_b_id": player_b_id,
            "player_b_name": names.get(player_b_id, f"球员{player_b_id}"),
            "matches": total_matches,
            "wins": stats["wins"],
            "win_rate": stats["wins"] / total_matches if total_matches else 0,
        })

    opponent_relationships = []
    for item in opponent_stats.values():
        item["win_rate"] = item["wins"] / item["matches"] if item["matches"] else 0
        item["avg_point_diff"] = (item["points_for"] - item["points_against"]) / item["matches"] if item["matches"] else 0
        opponent_relationships.append(item)

    return {
        "club_id": club_id,
        "player_id": player_id,
        "summary": {
            "matches": total,
            "wins": wins,
            "losses": total - wins,
            "win_rate": wins / total if total else 0,
            "avg_score": sum(i["team_score"] for i in recent_trend) / total if total else 0,
        },
        "recent_trend": recent_trend[-5:][::-1],
        "win_rate_curve": win_rate_curve,
        "opponent_relationships": sorted(opponent_relationships, key=lambda x: x["matches"], reverse=True),
        "partner_matrix": sorted(partner_matrix, key=lambda x: (x["matches"], x["win_rate"]), reverse=True),
    }
