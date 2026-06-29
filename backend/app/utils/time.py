"""时区工具：业务统计按中国时间，数据库存 UTC（naive）。"""

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

CN_TZ = ZoneInfo("Asia/Shanghai")


def utc_now_naive() -> datetime:
    """当前 UTC 时间（无时区标记，与数据库 naive UTC 一致）。"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def start_of_today_cn_naive_utc() -> datetime:
    """今天 0 点（北京时间）对应的 UTC naive，用于和库内 UTC 时间比较。"""
    now_cn = datetime.now(CN_TZ)
    start_cn = now_cn.replace(hour=0, minute=0, second=0, microsecond=0)
    return start_cn.astimezone(timezone.utc).replace(tzinfo=None)


def cn_date_to_utc_start(day: date) -> datetime:
    """某一天（北京时间）0 点 → UTC naive。"""
    start_cn = datetime(day.year, day.month, day.day, tzinfo=CN_TZ)
    return start_cn.astimezone(timezone.utc).replace(tzinfo=None)


def utc_naive_to_cn_date(dt: datetime | None) -> date | None:
    if dt is None:
        return None
    aware = dt.replace(tzinfo=timezone.utc)
    return aware.astimezone(CN_TZ).date()


def serialize_utc_datetime(dt: datetime | None) -> str | None:
    """API 输出：明确标记为 UTC，避免前端把无时区字符串当本地时间。"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
