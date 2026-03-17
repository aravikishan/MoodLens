"""Shared pytest fixtures for MoodLens tests."""

import pytest

from app import create_app
from config import TestConfig
from models.database import db as _db


@pytest.fixture(scope="session")
def app():
    """Create application for testing."""
    app = create_app(config_class=TestConfig)
    yield app


@pytest.fixture(scope="function")
def db(app):
    """Provide a clean database for each test."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.rollback()
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app, db):
    """Flask test client with clean DB."""
    with app.test_client() as c:
        with app.app_context():
            yield c


@pytest.fixture()
def db_session(db):
    """Convenience alias for db.session."""
    return db.session
