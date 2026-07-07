from datetime import datetime, timezone

from sqlalchemy import or_, text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session, joinedload

from app.models.competition import Competition, CompetitionPlayer, Match, Round
from app.models.player import Player, ClubMember
from app.models.user import User
from app.database import sync_player_id_sequence
from app.services.format_engine import get_engine
from app.utils.scoring import is_final_score, validate_score_pair

FORMAT_PLAYER_COUNTS: dict[str, list[int]] = {
    "singles_rotation": [2, 3, 4, 5, 6, 7, 8],
    "doubles_rotation": [4, 6, 8],
    "eight_player_rotation": [8],
    "four_player_rotation": [4],
    "knockout": [4, 8, 16],
}


def create_competition(
    db: Session, name: str, club_id: int | None, format: str,
    courts: int, player_ids: list[int], scheduled_at,
    open_signup: bool = False, is_public: bool = False,
    max_players: int | None = None, signup_deadline=None, creator_user_id: int | None = None,
) -> Competition:
    """创建比赛。club_id 为 None 时表示大厅/公开比赛（无需加入俱乐部即可参加）。"""
    if max_players is not None and max_players < 2:
        raise ValueError("报名人数上限不能小于 2")
    if open_signup and max_players is not None:
        _validate_format_player_count(format, max_players, "报名人数上限")

    # 大厅比赛必须开放报名且公开
    if club_id is None:
        open_signup = True
        is_public = True

    comp = Competition(
        name=name, club_id=club_id, format=format,
        courts=courts, scheduled_at=scheduled_at,
        status="open" if open_signup else "pending",
        is_public=is_public,
        max_players=max_players,
        signup_deadline=signup_deadline,
    )
    db.add(comp)
    db.flush()

    if open_signup:
        if creator_user_id is None:
            raise ValueError("开放报名比赛需要创建者信息")
        creator_player = _ensure_player_for_user(db, creator_user_id)
        db.add(CompetitionPlayer(competition_id=comp.id, player_id=creator_player.id))
    else:
        # 非报名模式必须有所属俱乐部才能验证球员
        if club_id is None:
            raise ValueError("非报名模式必须指定俱乐部")
        # 校验所有球员是否属于该俱乐部
        if not player_ids:
            raise ValueError("非报名模式必须选择参赛球员")
        valid_count = db.query(ClubMember).filter(
            ClubMember.club_id == club_id,
            ClubMember.player_id.in_(player_ids),
        ).count()
        if valid_count != len(player_ids):
            raise ValueError("部分球员不属于该俱乐部")
        for pid in player_ids:
            db.add(CompetitionPlayer(competition_id=comp.id, player_id=pid))
        _build_rounds(db, comp.id, format, courts, player_ids)
        comp.status = "in_progress"

    db.commit()
    return _load_competition(db, comp.id)


def start_competition(db: Session, comp_id: int) -> Competition:
    comp = _get_or_404(db, comp_id)
    if comp.status not in {"pending", "open"}:
        raise ValueError("比赛已经开始或已结束")
    if comp.status == "open":
        player_ids = [cp.player_id for cp in comp.competition_players]
        _validate_format_player_count(comp.format, len(player_ids), "当前报名人数")
        _build_rounds(db, comp.id, comp.format, comp.courts, player_ids)
    comp.status = "in_progress"
    db.commit()
    return _load_competition(db, comp_id)


def record_score(db: Session, match_id: int, score_a: int, score_b: int, user_id: int) -> Match:
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise ValueError("对阵不存在")

    rnd = db.query(Round).filter(Round.id == match.round_id).first()
    if rnd:
        comp = db.query(Competition).filter(Competition.id == rnd.competition_id).first()
        if comp:
            if comp.club_id is None:
                participant = db.query(CompetitionPlayer).filter(
                    CompetitionPlayer.competition_id == comp.id,
                    CompetitionPlayer.player_id == user_id,
                ).first()
                if not participant:
                    raise ValueError("你不是该比赛的参赛选手，无法录入比分")
            else:
                member = db.query(ClubMember).filter(
                    ClubMember.club_id == comp.club_id,
                    ClubMember.player_id == user_id,
                ).first()
                if not member:
                    raise ValueError("你不在该比赛所属俱乐部中，无法录入比分")

    validate_score_pair(score_a, score_b)

    is_game_over = is_final_score(score_a, score_b)

    # 如果旧比分是有效终局比分，先回退统计数据
    old_score_was_final = (
        match.score_a is not None
        and match.score_b is not None
        and is_final_score(match.score_a, match.score_b)
    )
    if old_score_was_final:
        _revert_player_stats(db, match)

    match.score_a = score_a
    match.score_b = score_b
    match.recorded_at = datetime.now(timezone.utc)
    db.commit()

    # 只在有效终局比分时更新统计数据和检查自动完成
    if is_game_over:
        _update_player_stats(db, match)

    if is_game_over:
        rnd = db.query(Round).filter(Round.id == match.round_id).first()
        if rnd:
            comp = db.query(Competition).filter(Competition.id == rnd.competition_id).first()
            if comp and all(
                m.score_a is not None
                and m.score_b is not None
                and is_final_score(m.score_a, m.score_b)
                for rnd2 in comp.rounds
                for m in rnd2.matches
            ):
                comp.status = "completed"
                db.commit()

    return match


def record_competition_score(
    db: Session, comp_id: int, score_a: int, score_b: int, user_id: int,
) -> tuple[Match, int]:
    """为比赛录入比分：必要时自动开赛，并找到第一场未计分的对阵。"""
    comp = ensure_competition_ready_to_score(db, comp_id)
    for rnd in comp.rounds:
        for m in rnd.matches:
            if m.score_a is None:
                match = record_score(db, m.id, score_a, score_b, user_id)
                return match, m.id
    raise ValueError("该比赛所有对阵都已录入比分")


def _comp_has_unscored_match(comp: Competition) -> bool:
    return any(m.score_a is None for rnd in comp.rounds for m in rnd.matches)


def _comp_player_count(comp: Competition) -> int:
    return len(comp.competition_players or [])


def can_start_competition(comp: Competition) -> bool:
    if comp.status not in {"open", "pending"}:
        return False
    if comp.rounds:
        return False
    player_count = _comp_player_count(comp)
    valid_counts = FORMAT_PLAYER_COUNTS.get(comp.format, [2])
    return player_count in valid_counts


def ensure_competition_ready_to_score(db: Session, comp_id: int) -> Competition:
    comp = _load_competition(db, comp_id)
    if comp.status == "completed":
        raise ValueError("比赛已结束，无法录入比分")
    if comp.rounds and _comp_has_unscored_match(comp):
        return comp
    if can_start_competition(comp):
        return start_competition(db, comp_id)
    if comp.status in {"open", "pending"} and not comp.rounds:
        valid = FORMAT_PLAYER_COUNTS.get(comp.format, [2])
        raise ValueError(
            f"比赛尚未开赛：当前 {_comp_player_count(comp)} 人报名，"
            f"该赛制需要 {'/'.join(map(str, valid))} 人才能开始计分"
        )
    raise ValueError("该比赛当前不可录入比分")


def list_scorable_competitions(db: Session, user_id: int) -> list[dict]:
    """列出用户参与、可计分或即将可计分的比赛（按最近创建排序）。"""
    competitions = (
        db.query(Competition)
        .join(CompetitionPlayer, CompetitionPlayer.competition_id == Competition.id)
        .options(joinedload(Competition.rounds).joinedload(Round.matches))
        .options(joinedload(Competition.competition_players))
        .filter(CompetitionPlayer.player_id == user_id)
        .filter(Competition.status != "completed")
        .order_by(Competition.created_at.desc(), Competition.id.desc())
        .all()
    )
    items: list[dict] = []
    for comp in competitions:
        player_count = _comp_player_count(comp)
        valid_counts = FORMAT_PLAYER_COUNTS.get(comp.format, [2])
        item = {
            "id": comp.id,
            "name": comp.name,
            "club_id": comp.club_id,
            "format": comp.format,
            "status": comp.status,
            "player_count": player_count,
            "required_players": valid_counts,
        }
        if comp.rounds and _comp_has_unscored_match(comp):
            item["ready_to_score"] = True
            item["message"] = "可直接计分"
            items.append(item)
        elif can_start_competition(comp):
            item["ready_to_score"] = True
            item["needs_start"] = True
            item["message"] = f"已报名 {player_count} 人，可开赛并计分"
            items.append(item)
        elif comp.status in {"open", "pending"} and not comp.rounds:
            item["ready_to_score"] = False
            item["message"] = (
                f"报名中 {player_count} 人，还需 "
                f"{'/'.join(str(n) for n in valid_counts)} 人才能开赛"
            )
            items.append(item)
    return items


def record_latest_score(
    db: Session, score_a: int, score_b: int, user_id: int,
) -> tuple[Match, int, int]:
    """为最近一场可计分的比赛录入比分（必要时自动开赛）。"""
    items = list_scorable_competitions(db, user_id)
    ready = [i for i in items if i.get("ready_to_score")]
    if not ready:
        if items:
            details = "；".join(f"「{i['name']}」(id={i['id']}): {i['message']}" for i in items[:3])
            raise ValueError(f"暂无可直接计分的比赛。{details}")
        raise ValueError("你还没有可计分的比赛，请先创建或加入比赛")
    target_id = ready[0]["id"]
    match, match_id = record_competition_score(db, target_id, score_a, score_b, user_id)
    return match, match_id, target_id


def get_competition(db: Session, comp_id: int) -> Competition:
    return _load_competition(db, comp_id)


def list_my_competitions(db: Session, user_id: int) -> list[dict]:
    competitions = (
        db.query(Competition)
        .join(CompetitionPlayer, CompetitionPlayer.competition_id == Competition.id)
        .options(joinedload(Competition.rounds).joinedload(Round.matches))
        .filter(CompetitionPlayer.player_id == user_id)
        .order_by(Competition.created_at.desc(), Competition.id.desc())
        .all()
    )
    items: list[dict] = []
    for comp in competitions:
        wins = 0
        losses = 0
        matches = 0
        for rnd in comp.rounds:
            for m in rnd.matches:
                if user_id not in (m.team_a or []) and user_id not in (m.team_b or []):
                    continue
                if m.score_a is None or m.score_b is None:
                    continue
                matches += 1
                if user_id in (m.team_a or []):
                    if m.score_a > m.score_b:
                        wins += 1
                    else:
                        losses += 1
                else:
                    if m.score_b > m.score_a:
                        wins += 1
                    else:
                        losses += 1
        items.append({
            "id": comp.id,
            "name": comp.name,
            "club_id": comp.club_id,
            "format": comp.format,
            "status": comp.status,
            "created_at": comp.created_at,
            "scheduled_at": comp.scheduled_at,
            "my_matches": matches,
            "my_wins": wins,
            "my_losses": losses,
            "my_win_rate": wins / matches if matches else 0,
        })
    return items


def list_open_competitions(db: Session, user_id: int, q: str = "") -> list[Competition]:
    query = db.query(Competition).options(
        joinedload(Competition.competition_players).joinedload(CompetitionPlayer.player),
    ).filter(Competition.status == "open")
    if q.strip():
        keyword = q.strip()
        query = query.outerjoin(
            CompetitionPlayer, CompetitionPlayer.competition_id == Competition.id
        ).outerjoin(
            Player, Player.id == CompetitionPlayer.player_id
        ).filter(
            or_(
                Competition.name.contains(keyword),
                Player.name.contains(keyword),
            )
        ).distinct()
    query = query.filter(
        or_(
            Competition.is_public.is_(True),
            db.query(ClubMember.id).filter(
                ClubMember.club_id == Competition.club_id,
                ClubMember.player_id == user_id,
            ).exists(),
        )
    )
    competitions = query.order_by(Competition.created_at.desc(), Competition.id.desc()).all()
    for comp in competitions:
        players = sorted(comp.competition_players or [], key=lambda cp: cp.id)
        creator = players[0].player.name if players and players[0].player else None
        setattr(comp, "creator_name", creator)
        setattr(comp, "my_joined", any(cp.player_id == user_id for cp in players))
    return competitions


def join_open_competition(db: Session, comp_id: int, user_id: int) -> Competition:
    try:
        # 报名热点场景：限制锁等待，避免长时间阻塞导致前端无反馈
        if "postgresql" in str(db.bind.url):
            db.execute(text("SET LOCAL lock_timeout = '1500ms'"))

        comp = db.query(Competition).filter(Competition.id == comp_id).with_for_update().first()
        if not comp:
            raise ValueError("比赛不存在")
        if comp.status != "open":
            raise ValueError("该比赛不在报名中")
        if comp.signup_deadline and datetime.now(timezone.utc) > _as_utc(comp.signup_deadline):
            raise ValueError("报名已截止")

        is_member = db.query(ClubMember).filter(
            ClubMember.club_id == comp.club_id,
            ClubMember.player_id == user_id,
        ).first() is not None
        if not comp.is_public and not is_member:
            raise ValueError("该比赛仅俱乐部成员可报名")

        player = _ensure_player_for_user(db, user_id)
        existing = db.query(CompetitionPlayer).filter(
            CompetitionPlayer.competition_id == comp_id,
            CompetitionPlayer.player_id == player.id,
        ).first()
        if existing:
            raise ValueError("你已报名该比赛")

        if comp.max_players is not None:
            count = db.query(CompetitionPlayer).filter(CompetitionPlayer.competition_id == comp_id).count()
            if count >= comp.max_players:
                raise ValueError("该比赛报名人数已满")

        db.add(CompetitionPlayer(competition_id=comp_id, player_id=player.id))
        db.commit()
        return _load_competition(db, comp_id)
    except OperationalError as e:
        db.rollback()
        if "lock timeout" in str(e).lower():
            raise ValueError("当前报名拥挤，请稍后重试")
        raise
    except IntegrityError:
        db.rollback()
        # 唯一约束兜底，保证并发下不会重复报名
        raise ValueError("你已报名该比赛")


def leave_open_competition(db: Session, comp_id: int, user_id: int) -> Competition:
    try:
        if "postgresql" in str(db.bind.url):
            db.execute(text("SET LOCAL lock_timeout = '1500ms'"))

        comp = db.query(Competition).filter(Competition.id == comp_id).with_for_update().first()
        if not comp:
            raise ValueError("比赛不存在")
        if comp.status != "open":
            raise ValueError("比赛已开始或已结束，无法退赛")

        cp = db.query(CompetitionPlayer).filter(
            CompetitionPlayer.competition_id == comp_id,
            CompetitionPlayer.player_id == user_id,
        ).first()
        if not cp:
            raise ValueError("你未报名该比赛")

        db.delete(cp)
        db.commit()
        return _load_competition(db, comp_id)
    except OperationalError as e:
        db.rollback()
        if "lock timeout" in str(e).lower():
            raise ValueError("当前操作拥挤，请稍后重试")
        raise


def _load_competition(db: Session, comp_id: int) -> Competition:
    comp = db.query(Competition).options(
        joinedload(Competition.rounds).joinedload(Round.matches),
        joinedload(Competition.competition_players).joinedload(CompetitionPlayer.player),
    ).filter(Competition.id == comp_id).first()
    if not comp:
        raise ValueError("比赛不存在")
    return comp


def _ensure_player_for_user(db: Session, user_id: int) -> Player:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("用户不存在")
    player = db.query(Player).filter(Player.id == user_id).first()
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


def _build_rounds(db: Session, comp_id: int, format: str, courts: int, player_ids: list[int]) -> None:
    if not player_ids:
        raise ValueError("报名人数不足，无法开始比赛")
    engine = get_engine(format)
    rounds_data = engine.generate(player_ids, courts)
    for round_number, round_matches in enumerate(rounds_data):
        rnd = Round(competition_id=comp_id, round_number=round_number + 1)
        db.add(rnd)
        db.flush()
        for m in round_matches:
            db.add(Match(
                round_id=rnd.id, court=m.court,
                team_a=m.team_a, team_b=m.team_b,
            ))


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _validate_format_player_count(format_name: str, count: int, subject: str) -> None:
    valid_counts = FORMAT_PLAYER_COUNTS.get(format_name)
    if not valid_counts:
        return
    if count in valid_counts:
        return
    if len(valid_counts) > 3:
        expected = f"{min(valid_counts)}-{max(valid_counts)} 人"
    else:
        expected = " / ".join(str(n) for n in valid_counts) + " 人"
    raise ValueError(f"{subject}与赛制不匹配：{format_name} 需要 {expected}，当前为 {count} 人")


def _get_or_404(db: Session, comp_id: int) -> Competition:
    comp = db.query(Competition).filter(Competition.id == comp_id).first()
    if not comp:
        raise ValueError("比赛不存在")
    return comp


def _update_player_stats(db: Session, match: Match):
    if match.score_a is None:
        return
    team_a_ids = match.team_a
    team_b_ids = match.team_b
    a_won = match.score_a > match.score_b
    diff = match.score_a - match.score_b
    for pid in team_a_ids + team_b_ids:
        player = db.query(Player).filter(Player.id == pid).first()
        if player:
            player.total_matches = (player.total_matches or 0) + 1
            if (pid in team_a_ids and a_won) or (pid in team_b_ids and not a_won):
                player.wins = (player.wins or 0) + 1
            player.win_rate = player.wins / player.total_matches if player.total_matches > 0 else 0
            # 净胜分：team_a 获得 +diff，team_b 获得 -diff
            if pid in team_a_ids:
                player.point_diff = (player.point_diff or 0) + diff
            else:
                player.point_diff = (player.point_diff or 0) - diff
            db.add(player)
    db.commit()


def _revert_player_stats(db: Session, match: Match):
    """回退一场比赛的球员统计数据（用于比分修改）"""
    if match.score_a is None:
        return
    team_a_ids = match.team_a
    team_b_ids = match.team_b
    a_won = match.score_a > match.score_b
    diff = match.score_a - match.score_b
    for pid in team_a_ids + team_b_ids:
        player = db.query(Player).filter(Player.id == pid).first()
        if player:
            player.total_matches = max(0, (player.total_matches or 0) - 1)
            if (pid in team_a_ids and a_won) or (pid in team_b_ids and not a_won):
                player.wins = max(0, (player.wins or 0) - 1)
            player.win_rate = player.wins / player.total_matches if player.total_matches > 0 else 0
            if pid in team_a_ids:
                player.point_diff = (player.point_diff or 0) - diff
            else:
                player.point_diff = (player.point_diff or 0) + diff
            db.add(player)
    db.commit()


def _is_score_final(score_a: int | None, score_b: int | None) -> bool:
    """判断比分是否为有效的一局终局比分"""
    if score_a is None or score_b is None:
        return False
    return is_final_score(score_a, score_b)


def finish_competition(db: Session, comp_id: int) -> Competition:
    comp = _get_or_404(db, comp_id)
    if comp.status == "pending":
        raise ValueError("比赛尚未开始")
    comp.status = "completed"
    db.commit()
    return comp
