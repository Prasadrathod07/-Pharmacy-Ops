"""Unit tests for app.core.database.is_transient_conflict.

Triggering a real MySQL deadlock/lock-wait-timeout deterministically in an
integration test is impractical (it requires holding a lock open across a
timing window), so the error-code classification logic is verified directly
here instead.
"""
from types import SimpleNamespace

from sqlalchemy.exc import OperationalError

from app.core.database import is_transient_conflict


def _make_operational_error(mysql_errno: int | None) -> OperationalError:
    orig = SimpleNamespace(args=(mysql_errno, "some message")) if mysql_errno is not None else SimpleNamespace(args=())
    return OperationalError("SELECT 1", {}, orig)


def test_lock_wait_timeout_is_transient_conflict():
    assert is_transient_conflict(_make_operational_error(1205)) is True


def test_deadlock_found_is_transient_conflict():
    assert is_transient_conflict(_make_operational_error(1213)) is True


def test_unrelated_operational_error_is_not_transient_conflict():
    assert is_transient_conflict(_make_operational_error(2003)) is False  # e.g. "can't connect"


def test_error_with_no_args_is_not_transient_conflict():
    assert is_transient_conflict(_make_operational_error(None)) is False
