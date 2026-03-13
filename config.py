"""Application configuration for MoodLens."""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Default Flask configuration."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "moodlens-dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'moodlens.db')}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PORT = int(os.environ.get("PORT", 8008))
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
    MAX_CONTENT_LENGTH = 16 * 1024  # 16 KB max request


class TestConfig(Config):
    """Testing configuration -- uses in-memory SQLite."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = "test-secret-key"
