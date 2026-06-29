from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.agent_conversation import AgentConversation
from app.models.club import Club
from app.models.competition import Competition
from app.models.player import ClubMember, Player
from app.models.user import User
from app.utils.time import (
    CN_TZ,
    cn_date_to_utc_start,
    serialize_utc_datetime,
    start_of_today_cn_naive_utc,
    utc_naive_to_cn_date,
    utc_now_naive,
)


def _start_of_today() -> datetime:
    """今日 0 点（北京时间）对应的 UTC naive。"""
    return start_of_today_cn_naive_utc()


def get_overview_stats(db: Session) -> dict:
    today = _start_of_today()
    week_ago = today - timedelta(days=7)
    active_since = utc_now_naive() - timedelta(days=7)

    total_users = db.query(func.count(User.id)).scalar() or 0
    today_registrations = db.query(func.count(User.id)).filter(User.created_at >= today).scalar() or 0
    week_registrations = db.query(func.count(User.id)).filter(User.created_at >= week_ago).scalar() or 0
    total_clubs = db.query(func.count(Club.id)).scalar() or 0
    total_competitions = db.query(func.count(Competition.id)).scalar() or 0
    competitions_in_progress = (
        db.query(func.count(Competition.id)).filter(Competition.status == "in_progress").scalar() or 0
    )
    completed_competitions = (
        db.query(func.count(Competition.id)).filter(Competition.status == "completed").scalar() or 0
    )
    agent_messages_total = db.query(func.count(AgentConversation.id)).scalar() or 0
    agent_messages_today = (
        db.query(func.count(AgentConversation.id)).filter(AgentConversation.created_at >= today).scalar() or 0
    )
    active_users_7d = (
        db.query(func.count(func.distinct(AgentConversation.user_id)))
        .filter(AgentConversation.created_at >= active_since)
        .scalar()
        or 0
    )

    return {
        "total_users": total_users,
        "today_registrations": today_registrations,
        "week_registrations": week_registrations,
        "total_clubs": total_clubs,
        "total_competitions": total_competitions,
        "competitions_in_progress": competitions_in_progress,
        "completed_competitions": completed_competitions,
        "agent_messages_total": agent_messages_total,
        "agent_messages_today": agent_messages_today,
        "active_users_7d": active_users_7d,
    }


def get_registration_trend(db: Session, days: int = 30) -> list[dict]:
    days = max(1, min(days, 90))
    today_cn = datetime.now(CN_TZ).date()
    start_day_cn = today_cn - timedelta(days=days - 1)
    start_utc = cn_date_to_utc_start(start_day_cn)

    users = (
        db.query(User.created_at)
        .filter(User.created_at >= start_utc, User.created_at.isnot(None))
        .all()
    )
    counts: dict[date, int] = {}
    for (created_at,) in users:
        day = utc_naive_to_cn_date(created_at)
        if day is None:
            continue
        counts[day] = counts.get(day, 0) + 1

    trend = []
    for i in range(days):
        day = start_day_cn + timedelta(days=i)
        trend.append({"date": day, "count": counts.get(day, 0)})
    return trend


def list_users(db: Session, page: int = 1, page_size: int = 20, search: str = "") -> dict:
    page = max(1, page)
    page_size = max(1, min(page_size, 100))

    query = db.query(User)
    if search.strip():
        like = f"%{search.strip()}%"
        query = query.filter((User.username.ilike(like)) | (User.name.ilike(like)))

    total = query.count()
    users = query.order_by(User.id.desc()).offset((page - 1) * page_size).limit(page_size).all()

    user_ids = [u.id for u in users]
    club_counts: dict[int, int] = {}
    agent_counts: dict[int, int] = {}
    if user_ids:
        for uid, cnt in (
            db.query(ClubMember.player_id, func.count(ClubMember.id))
            .filter(ClubMember.player_id.in_(user_ids))
            .group_by(ClubMember.player_id)
            .all()
        ):
            club_counts[uid] = cnt
        for uid, cnt in (
            db.query(AgentConversation.user_id, func.count(AgentConversation.id))
            .filter(AgentConversation.user_id.in_(user_ids))
            .group_by(AgentConversation.user_id)
            .all()
        ):
            agent_counts[uid] = cnt

    items = []
    for user in users:
        items.append({
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "is_admin": bool(user.is_admin),
            "created_at": serialize_utc_datetime(user.created_at),
            "club_count": club_counts.get(user.id, 0),
            "agent_messages": agent_counts.get(user.id, 0),
        })

    return {"items": items, "total": total, "page": page, "page_size": page_size}


def list_recent_competitions(db, limit: int = 10) -> dict:
    limit = max(1, min(limit, 50))
    competitions = (
        db.query(Competition)
        .order_by(Competition.created_at.desc(), Competition.id.desc())
        .limit(limit)
        .all()
    )
    items = []
    for comp in competitions:
        # 安全计算 player_count，过滤掉 player_id <= 0 的幽灵记录
        safe_count = 0
        if comp.competition_players:
            safe_count = sum(
                1 for cp in comp.competition_players
                if cp.player_id and cp.player_id > 0
            )
        items.append({
            "id": comp.id,
            "name": comp.name,
            "club_id": comp.club_id,
            "status": comp.status,
            "player_count": safe_count,
            "created_at": serialize_utc_datetime(comp.created_at),
        })
    return {"items": items}


def sync_all_user_players(db: Session) -> int:
    """将 users.name 同步到同 id 的 players.name，修复历史数据"""
    updated = 0
    for user in db.query(User).all():
        player = db.query(Player).filter(Player.id == user.id).first()
        if not player:
            continue
        changed = False
        if player.name != user.name:
            player.name = user.name
            changed = True
        if user.gender and player.gender != user.gender:
            player.gender = user.gender
            changed = True
        if changed:
            updated += 1
    if updated:
        db.commit()
    return updated


def sync_admin_users(db: Session, usernames: list[str]) -> None:
    if not usernames:
        return
    db.query(User).filter(User.username.in_(usernames)).update({User.is_admin: True}, synchronize_session=False)
    db.commit()
