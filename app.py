"""MoodLens -- Flask application entry point.

A mood journaling application with lexicon-based sentiment analysis,
emotion tracking, and wellness trend analytics.
"""

import logging
import os
import sys

from flask import Flask

from config import Config, TestConfig
from models.database import init_db, get_db
from routes.api import api_bp
from routes.views import views_bp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def create_app(config_class=None) -> Flask:
    """Application factory -- create and configure the Flask app."""
    app = Flask(__name__)

    if config_class is None:
        config_class = Config
    app.config.from_object(config_class)

    # v1.0.1 - Ensure instance directory exists for SQLite
    os.makedirs(os.path.join(app.root_path, "instance"), exist_ok=True)

    # Initialize components database
    init_db(app)

    # Register blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(views_bp)

    # Seed the database with sample data when not testing
    if not app.config.get("TESTING"):
        with app.app_context():
            try:
                from services.analytics import seed_database
                count = seed_database(get_db())
                if count:
                    logger.info("Seeded database with %d sample entries", count)
            except Exception as exc:
                logger.warning("Could not seed database: %s", exc)

    logger.info("MoodLens application created successfully")
    return app


# ── Entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 8008))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    logger.info("Starting MoodLens on http://0.0.0.0:%d", port)
    app.run(host="0.0.0.0", port=port, debug=debug)
