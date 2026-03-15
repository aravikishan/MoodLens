"""HTML page-rendering routes for MoodLens."""

from flask import Blueprint, render_template

views_bp = Blueprint("views", __name__)


@views_bp.route("/")
def index():
    """Dashboard with mood overview and recent entries."""
    return render_template("index.html")


@views_bp.route("/journal")
def journal():
    """Write a new journal entry page."""
    return render_template("journal.html")


@views_bp.route("/entries")
def entries():
    """Browse and search past entries."""
    return render_template("entries.html")


@views_bp.route("/analytics")
def analytics():
    """Trend charts and mood insights."""
    return render_template("analytics.html")


@views_bp.route("/about")
def about():
    """About MoodLens page."""
    return render_template("about.html")
