from datetime import date, datetime, timezone

from app.utils.time import (
    cn_date_to_utc_start,
    serialize_utc_datetime,
    utc_naive_to_cn_date,
)


def test_utc_naive_to_cn_date():
    # 北京时间 2026-07-02 09:30 = UTC 2026-07-02 01:30
    dt = datetime(2026, 7, 2, 1, 30, 0)
    assert utc_naive_to_cn_date(dt) == date(2026, 7, 2)


def test_serialize_utc_datetime_adds_z_suffix():
    dt = datetime(2026, 7, 2, 1, 30, 0)
    assert serialize_utc_datetime(dt) == "2026-07-02T01:30:00Z"


def test_cn_date_to_utc_start():
    # 北京 7月2日 0点 = UTC 7月1日 16点
    start = cn_date_to_utc_start(date(2026, 7, 2))
    assert start == datetime(2026, 7, 1, 16, 0, 0)
