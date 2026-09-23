"""Shared fixtures for integration tests running against the real MySQL database.

Each test runs inside a transaction that is rolled back afterward, so tests
never leave residue in the shared development database.
"""
import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import engine


@pytest.fixture()
def db_session() -> Session:
    connection = engine.connect()
    transaction = connection.begin()
    TestSessionLocal = sessionmaker(bind=connection)
    session = TestSessionLocal()

    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()
