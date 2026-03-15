"""REST API endpoints for MoodLens."""

from flask import Blueprint, jsonify, request

from models.database import get_db
from models.schemas import JournalEntry
from services.sentiment import analyze_sentiment, get_mood_color
from services.analytics import (
    save_entry,
    get_entries,
    get_entry_by_id,
    delete_entry,
    search_entries,
    get_trends,
    get_stats,
    get_word_frequencies,
    get_wellness_suggestions,
)

api_bp = Blueprint("api", __name__, url_prefix="/api")


# ── Entry CRUD ────────────────────────────────────────────────────────────


@api_bp.route("/entries", methods=["POST"])
def create_entry():
    """Create a new journal entry with sentiment analysis."""
    data = request.get_json(silent=True)
    if not data or not data.get("content", "").strip():
        return jsonify({"error": "Content is required"}), 400

    text = data["content"].strip()
    if len(text) > 5000:
        return jsonify({"error": "Content must be under 5000 characters"}), 400

    analysis = analyze_sentiment(text)
    analysis["mood_color"] = get_mood_color(analysis["mood_score"])

    db_session = get_db()
    entry = save_entry(db_session, text, analysis)

    return jsonify({
        "entry": entry.to_dict(),
        "analysis": analysis,
    }), 201


@api_bp.route("/entries", methods=["GET"])
def list_entries():
    """List journal entries with pagination and optional search."""
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)
    search_query = request.args.get("search", "", type=str).strip()
    emotion_filter = request.args.get("emotion", "", type=str).strip()

    limit = min(max(limit, 1), 100)
    offset = max(offset, 0)

    db_session = get_db()

    if search_query or emotion_filter:
        entries = search_entries(
            db_session,
            query=search_query,
            emotion=emotion_filter,
            limit=limit,
            offset=offset,
        )
    else:
        entries = get_entries(db_session, limit=limit, offset=offset)

    return jsonify({"entries": entries, "count": len(entries)})


@api_bp.route("/entries/<int:entry_id>", methods=["GET"])
def get_single_entry(entry_id):
    """Get a single journal entry by ID."""
    db_session = get_db()
    entry = get_entry_by_id(db_session, entry_id)
    if not entry:
        return jsonify({"error": "Entry not found"}), 404
    return jsonify({"entry": entry})


@api_bp.route("/entries/<int:entry_id>", methods=["DELETE"])
def remove_entry(entry_id):
    """Delete a journal entry by ID."""
    db_session = get_db()
    success = delete_entry(db_session, entry_id)
    if not success:
        return jsonify({"error": "Entry not found"}), 404
    return jsonify({"message": "Entry deleted", "id": entry_id})


# ── Analysis ──────────────────────────────────────────────────────────────


@api_bp.route("/analyze", methods=["POST"])
def analyze_text():
    """Analyze text sentiment without saving an entry."""
    data = request.get_json(silent=True)
    if not data or not data.get("content", "").strip():
        return jsonify({"error": "Content is required"}), 400

    text = data["content"].strip()
    analysis = analyze_sentiment(text)
    analysis["mood_color"] = get_mood_color(analysis["mood_score"])
    return jsonify({"analysis": analysis})


# ── Trends & Stats ────────────────────────────────────────────────────────


@api_bp.route("/trends", methods=["GET"])
def mood_trends():
    """Get mood trends for a given number of days."""
    days = request.args.get("days", 30, type=int)
    days = min(max(days, 1), 365)
    db_session = get_db()
    trends = get_trends(db_session, days=days)
    return jsonify({"trends": trends, "days": days})


@api_bp.route("/stats", methods=["GET"])
def overall_stats():
    """Get overall mood statistics."""
    db_session = get_db()
    stats = get_stats(db_session)
    return jsonify({"stats": stats})


@api_bp.route("/word-cloud", methods=["GET"])
def word_cloud():
    """Get positive and negative word frequencies for word cloud."""
    db_session = get_db()
    frequencies = get_word_frequencies(db_session)
    return jsonify({"words": frequencies})


@api_bp.route("/suggestions", methods=["GET"])
def suggestions():
    """Get wellness suggestions based on recent mood patterns."""
    db_session = get_db()
    tips = get_wellness_suggestions(db_session)
    return jsonify({"suggestions": tips})


# ── Health ────────────────────────────────────────────────────────────────


@api_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "MoodLens"})
