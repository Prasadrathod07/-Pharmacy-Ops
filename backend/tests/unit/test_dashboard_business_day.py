"""Unit tests for the business-day boundary calculation (master spec §9,
§36 "Use BUSINESS_TIMEZONE. Avoid naive date handling.").
"""
from datetime import datetime, timezone

from app.services.dashboard_service import _business_day_bounds_utc_naive


def test_utc_business_day_is_midnight_to_midnight_utc():
    now = datetime(2026, 9, 23, 14, 30, tzinfo=timezone.utc)
    start, end = _business_day_bounds_utc_naive("UTC", now)

    assert start == datetime(2026, 9, 23, 0, 0, 0)
    assert end == datetime(2026, 9, 24, 0, 0, 0)
    assert start.tzinfo is None and end.tzinfo is None


def test_non_utc_timezone_shifts_the_day_boundary():
    # 2026-09-23 02:00 UTC is already 2026-09-23 07:30 in Asia/Kolkata
    # (UTC+5:30), so the Kolkata business day started 5.5h earlier in UTC
    # terms than the UTC business day would have.
    now = datetime(2026, 9, 23, 2, 0, tzinfo=timezone.utc)
    start, end = _business_day_bounds_utc_naive("Asia/Kolkata", now)

    assert start == datetime(2026, 9, 22, 18, 30, 0)
    assert end == datetime(2026, 9, 23, 18, 30, 0)


def test_timestamp_just_before_local_midnight_falls_in_previous_business_day():
    # 2026-09-22 23:59 UTC is 2026-09-23 05:29 in Kolkata -> still "today"
    # (2026-09-23) in Kolkata terms, even though it's "yesterday" in UTC.
    now = datetime(2026, 9, 22, 23, 59, tzinfo=timezone.utc)
    start, end = _business_day_bounds_utc_naive("Asia/Kolkata", now)

    assert start == datetime(2026, 9, 22, 18, 30, 0)
    assert end == datetime(2026, 9, 23, 18, 30, 0)
    assert start <= now.replace(tzinfo=None) < end
