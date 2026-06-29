"""球员数据分析服务：搭档统计、智能分组"""

from sqlalchemy.orm import Session

from app.models.competition import Competition, CompetitionPlayer, Match, Round
from app.models.player import Player, ClubMember


def get_partner_stats(db: Session, player_id: int) -> list[dict]:
    """查询该球员与不同搭档的合作统计"""
    # 找所有该球员参与的比赛
    sub = db.query(CompetitionPlayer.competition_id).filter(
        CompetitionPlayer.player_id == player_id
    ).subquery()
    match_ids = db.query(Match.id).join(Round).filter(
        Round.competition_id.in_(sub),
    ).subquery()

    matches = db.query(Match).filter(Match.id.in_(match_ids)).all()

    partner_stats: dict[int, dict] = {}
    for m in matches:
        if m.score_a is None:
            continue
        teams = [(m.team_a, m.team_b, m.score_a, m.score_b),
                 (m.team_b, m.team_a, m.score_b, m.score_a)]
        for team, opp_team, team_score, opp_score in teams:
            if player_id not in team:
                continue
            partner_id = team[0] if team[1] == player_id else team[1]
            if partner_id == player_id:
                continue
            won = team_score > opp_score
            entry = partner_stats.setdefault(partner_id, {
                "total": 0, "wins": 0, "partner_id": partner_id,
                "partner_name": "",
            })
            entry["total"] += 1
            if won:
                entry["wins"] += 1

    for pid, s in partner_stats.items():
        s["win_rate"] = s["wins"] / s["total"] if s["total"] > 0 else 0
        partner = db.query(Player).filter(Player.id == pid).first()
        if partner:
            s["partner_name"] = partner.name

    return sorted(partner_stats.values(), key=lambda x: (x["total"], x["win_rate"]), reverse=True)


def suggest_balanced_teams(db: Session, club_id: int, player_ids: list[int] | None = None) -> dict:
    """根据球员等级和胜率，建议平衡分组"""
    if player_ids:
        players = db.query(Player).filter(Player.id.in_(player_ids)).all()
    else:
        player_ids = [r[0] for r in db.query(ClubMember.player_id).filter(
            ClubMember.club_id == club_id).all()]
        players = db.query(Player).filter(Player.id.in_(player_ids)).all()

    if len(players) < 4:
        return {"error": "至少需要 4 名球员才能分组"}

    # 按胜率排序
    sorted_players = sorted(players, key=lambda p: (p.win_rate or 0), reverse=True)
    n = len(sorted_players)

    # 蛇形分组: 1,4,5,8,... 一组; 2,3,6,7,... 一组
    team_a_ids = []
    team_b_ids = []
    for i in range(0, n, 4):
        if i < n:
            team_a_ids.append(sorted_players[i].id)
        if i + 3 < n:
            team_a_ids.append(sorted_players[i + 3].id)
        if i + 1 < n:
            team_b_ids.append(sorted_players[i + 1].id)
        if i + 2 < n:
            team_b_ids.append(sorted_players[i + 2].id)

    player_map = {p.id: p for p in players}
    return {
        "team_a": [{"id": pid, "name": player_map[pid].name, "win_rate": player_map[pid].win_rate or 0} for pid in team_a_ids],
        "team_b": [{"id": pid, "name": player_map[pid].name, "win_rate": player_map[pid].win_rate or 0} for pid in team_b_ids],
        "method": "蛇形分组（按胜率排序后交替分配）",
    }
