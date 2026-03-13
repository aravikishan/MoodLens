"""SQLAlchemy database setup for MoodLens."""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    """Initialize the database with the Flask application."""
    db.init_app(app)
    with app.app_context():
        from models.schemas import JournalEntry, MoodRecord  # noqa: F401
        db.create_all()


def get_db():
    """Return the current database session."""
    return db.session


def reset_db(app):
    """Drop and recreate all tables (used in tests)."""
    with app.app_context():
        db.drop_all()
        db.create_all()
