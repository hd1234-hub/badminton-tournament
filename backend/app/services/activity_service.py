from datetime import datetime, timezone

from sqlalchemy.orm import Session, joinedload

from app.models.competition import Activity, ActivitySignup
from app.models.player import ClubMember, Player
from app.models.user import User
from app.services import club_service, competition_service


FORMAT_COUNTS = {
    "four_player_rotation": [4],
    "eight_player_rotation": [8],
    "knockout": [4, 8, 16],
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _ensure_member_player(db: Session, club_id: int, user: User) -> Player:
    player = club_service._ensure_player(db, user)
    member = db.query(ClubMember).filter(
        ClubMember.club_id == club_id,
        ClubMember.player_id == player.id,
    ).first()
    if not member:
        raise ValueError("你不在该俱乐部中，无法报名")
    return player


def _load_activity(db: Session, activity_id: int) -> Activity:
    activity = db.query(Activity).options(
        joinedload(Activity.signups).joinedload(ActivitySignup.player)
    ).filter(Activity.id == activity_id).first()
    if not activity:
        raise ValueError("活动不存在")
    return activity


def _serialize(activity: Activity, user: User | None = None) -> dict:
    confirmed_count = sum(1 for s in activity.signups if s.status == "confirmed")
    waitlist_count = sum(1 for s in activity.signups if s.status == "waitlisted")
    my_signup_status = None
    if user:
        for s in activity.signups:
            if s.player_id == user.id and s.status != "cancelled":
                my_signup_status = s.status
                break
    return {
        "id": activity.id,
        "club_id": activity.club_id,
        "title": activity.title,
        "description": activity.description,
        "location": activity.location,
        "format": activity.format,
        "courts": activity.courts,
        "min_players": activity.min_players,
        "max_players": activity.max_players,
        "start_time": activity.start_time,
        "signup_deadline": activity.signup_deadline,
        "status": activity.status,
        "competition_id": activity.competition_id,
        "created_at": activity.created_at,
        "signups": [s for s in activity.signups if s.status != "cancelled"],
        "confirmed_count": confirmed_count,
        "waitlist_count": waitlist_count,
        "my_signup_status": my_signup_status,
    }


def create_activity(db: Session, user: User, data) -> dict:
    _ensure_member_player(db, data.club_id, user)
    if data.max_players < data.min_players:
        raise ValueError("最大人数不能小于最小人数")
    if data.format not in FORMAT_COUNTS:
        raise ValueError("不支持的赛制")
    valid_counts = FORMAT_COUNTS[data.format]
    if data.min_players not in valid_counts or data.max_players not in valid_counts:
        raise ValueError(f"{data.format} 需要 {valid_counts} 人")
    if _as_aware(data.signup_deadline) > _as_aware(data.start_time):
        raise ValueError("报名截止时间不能晚于开始时间")

    activity = Activity(
        club_id=data.club_id,
        title=data.title,
        description=data.description,
        location=data.location,
        format=data.format,
        courts=data.courts,
        min_players=data.min_players,
        max_players=data.max_players,
        start_time=data.start_time,
        signup_deadline=data.signup_deadline,
    )
    db.add(activity)
    db.commit()
    return _serialize(_load_activity(db, activity.id), user)


def list_club_activities(db: Session, club_id: int, user: User) -> list[dict]:
    _ensure_member_player(db, club_id, user)
    activities = db.query(Activity).options(
        joinedload(Activity.signups).joinedload(ActivitySignup.player)
    ).filter(Activity.club_id == club_id).order_by(Activity.start_time.desc()).all()
    return [_serialize(a, user) for a in activities]


def get_activity(db: Session, activity_id: int, user: User) -> dict:
    activity = _load_activity(db, activity_id)
    _ensure_member_player(db, activity.club_id, user)
    return _serialize(activity, user)


def signup(db: Session, activity_id: int, user: User) -> dict:
    activity = _load_activity(db, activity_id)
    player = _ensure_member_player(db, activity.club_id, user)
    if activity.status != "open":
        raise ValueError("活动已关闭报名")
    if _now() > _as_aware(activity.signup_deadline):
        raise ValueError("报名已截止")

    existing = db.query(ActivitySignup).filter(
        ActivitySignup.activity_id == activity_id,
        ActivitySignup.player_id == player.id,
    ).first()
    confirmed_count = db.query(ActivitySignup).filter(
        ActivitySignup.activity_id == activity_id,
        ActivitySignup.status == "confirmed",
    ).count()
    status = "confirmed" if confirmed_count < activity.max_players else "waitlisted"

    if existing:
        if existing.status != "cancelled":
            raise ValueError("你已报名该活动")
        existing.status = status
        existing.signed_up_at = _now()
    else:
        db.add(ActivitySignup(activity_id=activity_id, player_id=player.id, status=status))
    db.commit()
    return get_activity(db, activity_id, user)


def cancel_signup(db: Session, activity_id: int, user: User) -> dict:
    activity = _load_activity(db, activity_id)
    _ensure_member_player(db, activity.club_id, user)
    signup_row = db.query(ActivitySignup).filter(
        ActivitySignup.activity_id == activity_id,
        ActivitySignup.player_id == user.id,
        ActivitySignup.status.in_(["confirmed", "waitlisted"]),
    ).first()
    if not signup_row:
        raise ValueError("你还没有报名该活动")

    was_confirmed = signup_row.status == "confirmed"
    signup_row.status = "cancelled"
    if was_confirmed:
        next_waiting = db.query(ActivitySignup).filter(
            ActivitySignup.activity_id == activity_id,
            ActivitySignup.status == "waitlisted",
        ).order_by(ActivitySignup.signed_up_at).first()
        if next_waiting:
            next_waiting.status = "confirmed"
    db.commit()
    return get_activity(db, activity_id, user)


def generate_competition(db: Session, activity_id: int, user: User):
    activity = _load_activity(db, activity_id)
    _ensure_member_player(db, activity.club_id, user)
    if activity.competition_id:
        return competition_service.get_competition(db, activity.competition_id)

    player_ids = [s.player_id for s in activity.signups if s.status == "confirmed"]
    if len(player_ids) < activity.min_players:
        raise ValueError("确认报名人数不足，无法生成比赛")
    if len(player_ids) not in FORMAT_COUNTS[activity.format]:
        raise ValueError("确认报名人数不符合当前赛制")

    comp = competition_service.create_competition(
        db,
        activity.title,
        activity.club_id,
        activity.format,
        activity.courts,
        player_ids,
        activity.start_time,
    )
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    activity.competition_id = comp.id
    activity.status = "scheduled"
    db.commit()
    return competition_service.get_competition(db, comp.id)
