from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.competition import Activity, ActivitySignup, Competition, Match, Round
from app.models.notification import Notification
from app.models.player import ClubMember
from app.models.user import User


START_REMINDER_WINDOW = timedelta(hours=24)
UNRECORDED_SCORE_WINDOW = timedelta(hours=2)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _create_notification(
    db: Session,
    user_id: int,
    type: str,
    title: str,
    message: str,
    severity: str = "info",
    club_id: int | None = None,
    activity_id: int | None = None,
    competition_id: int | None = None,
    match_id: int | None = None,
    dedupe_key: str | None = None,
    expires_at: datetime | None = None,
):
    if dedupe_key:
        existing = db.query(Notification).filter(Notification.dedupe_key == dedupe_key).first()
        if existing:
            return
    db.add(Notification(
        user_id=user_id,
        club_id=club_id,
        activity_id=activity_id,
        competition_id=competition_id,
        match_id=match_id,
        type=type,
        title=title,
        message=message,
        severity=severity,
        dedupe_key=dedupe_key,
        expires_at=expires_at,
    ))


def _generate_activity_notifications(db: Session, user: User):
    player_id = user.id
    now = _now()
    memberships = db.query(ClubMember.club_id).filter(ClubMember.player_id == player_id).all()
    club_ids = [row[0] for row in memberships]
    if not club_ids:
        return

    activities = db.query(Activity).filter(
        Activity.club_id.in_(club_ids),
        Activity.status == "open",
    ).all()
    for activity in activities:
        start_time = _as_aware(activity.start_time)
        signup_deadline = _as_aware(activity.signup_deadline)
        if not start_time:
            continue

        signup = db.query(ActivitySignup).filter(
            ActivitySignup.activity_id == activity.id,
            ActivitySignup.player_id == player_id,
            ActivitySignup.status.in_(["confirmed", "waitlisted"]),
        ).first()
        confirmed_count = db.query(ActivitySignup).filter(
            ActivitySignup.activity_id == activity.id,
            ActivitySignup.status == "confirmed",
        ).count()

        if signup and now <= start_time <= now + START_REMINDER_WINDOW:
            _create_notification(
                db,
                user.id,
                "activity_start",
                "活动即将开始",
                f"{activity.title} 将在 24 小时内开始。",
                "info",
                club_id=activity.club_id,
                activity_id=activity.id,
                dedupe_key=f"activity_start:{activity.id}:{user.id}",
                expires_at=start_time + timedelta(hours=1),
            )

        if confirmed_count < activity.min_players and signup_deadline and now <= signup_deadline <= now + START_REMINDER_WINDOW:
            _create_notification(
                db,
                user.id,
                "activity_insufficient_players",
                "活动人数不足",
                f"{activity.title} 当前确认 {confirmed_count}/{activity.min_players} 人，报名截止临近。",
                "warning",
                club_id=activity.club_id,
                activity_id=activity.id,
                dedupe_key=f"activity_insufficient:{activity.id}:{user.id}",
                expires_at=signup_deadline + timedelta(hours=1),
            )


def _generate_score_notifications(db: Session, user: User):
    now = _now()
    memberships = db.query(ClubMember.club_id).filter(ClubMember.player_id == user.id).all()
    club_ids = [row[0] for row in memberships]
    if not club_ids:
        return

    competitions = db.query(Competition).filter(
        Competition.club_id.in_(club_ids),
        Competition.status == "in_progress",
    ).all()
    for comp in competitions:
        scheduled_at = _as_aware(comp.scheduled_at)
        if scheduled_at and now < scheduled_at + UNRECORDED_SCORE_WINDOW:
            continue
        unscored = db.query(Match).join(Round).filter(
            Round.competition_id == comp.id,
            Match.score_a.is_(None),
        ).all()
        for match in unscored:
            if user.id not in (match.team_a or []) + (match.team_b or []):
                continue
            _create_notification(
                db,
                user.id,
                "score_unrecorded",
                "比分待录入",
                f"{comp.name} 第 {match.round.round_number} 轮 {match.court} 号场比分还未录入。",
                "warning",
                club_id=comp.club_id,
                competition_id=comp.id,
                match_id=match.id,
                dedupe_key=f"score_unrecorded:{match.id}:{user.id}",
            )


def generate_notifications(db: Session, user: User):
    _generate_activity_notifications(db, user)
    _generate_score_notifications(db, user)
    db.commit()


def list_notifications(db: Session, user: User, unread_only: bool = False) -> list[Notification]:
    generate_notifications(db, user)
    query = db.query(Notification).filter(Notification.user_id == user.id)
    now = _now()
    query = query.filter((Notification.expires_at.is_(None)) | (Notification.expires_at > now))
    if unread_only:
        query = query.filter(Notification.read_at.is_(None))
    return query.order_by(Notification.created_at.desc()).limit(100).all()


def mark_read(db: Session, user: User, notification_id: int) -> Notification:
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user.id,
    ).first()
    if not notification:
        raise ValueError("通知不存在")
    notification.read_at = _now()
    db.commit()
    db.refresh(notification)
    return notification


def mark_all_read(db: Session, user: User) -> int:
    notifications = db.query(Notification).filter(
        Notification.user_id == user.id,
        Notification.read_at.is_(None),
    ).all()
    now = _now()
    for notification in notifications:
        notification.read_at = now
    db.commit()
    return len(notifications)
