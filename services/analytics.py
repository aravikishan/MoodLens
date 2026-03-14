"""Trend calculation, mood statistics, and data access for MoodLens."""

import json
import os
from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy import func

from models.schemas import JournalEntry, MoodRecord
from services.sentiment import (
    analyze_sentiment,
    extract_sentiment_words,
    get_mood_label,
)


# ── Entry CRUD ────────────────────────────────────────────────────────────


def save_entry(db_session, text: str, analysis: dict) -> JournalEntry:
    """Persist a journal entry with its analysis results."""
    entry = JournalEntry(
        content=text,
        mood_score=analysis["mood_score"],
        mood_label=analysis.get("mood_label", get_mood_label(analysis["mood_score"])),
        dominant_emotion=analysis["dominant_emotion"],
        emotions=analysis.get("emotion_breakdown", {}),
        word_count=analysis["word_count"],
        positive_count=analysis.get("positive_word_count", 0),
        negative_count=analysis.get("negative_word_count", 0),
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(entry)
    db_session.commit()
    return entry


def get_entries(db_session, limit: int = 50, offset: int = 0) -> list[dict]:
    """Return recent journal entries ordered by date descending."""
    entries = (
        db_session.query(JournalEntry)
        .order_by(JournalEntry.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [e.to_dict() for e in entries]


def get_entry_by_id(db_session, entry_id: int) -> dict | None:
    """Return a single entry by its primary key."""
    entry = db_session.get(JournalEntry, entry_id)
    return entry.to_dict() if entry else None


def delete_entry(db_session, entry_id: int) -> bool:
    """Delete an entry by ID. Returns True if found and deleted."""
    entry = db_session.get(JournalEntry, entry_id)
    if not entry:
        return False
    db_session.delete(entry)
    db_session.commit()
    return True


def search_entries(
    db_session,
    query: str = "",
    emotion: str = "",
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """Search entries by content keyword and/or emotion filter."""
    q = db_session.query(JournalEntry)
    if query:
        q = q.filter(JournalEntry.content.ilike(f"%{query}%"))
    if emotion:
        q = q.filter(JournalEntry.dominant_emotion == emotion)
    entries = (
        q.order_by(JournalEntry.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [e.to_dict() for e in entries]


# ── Trend analytics ──────────────────────────────────────────────────────


def get_trends(db_session, days: int = 30) -> dict:
    """Compute mood trends for the last *days* days.

    Returns: weekly_avg, monthly_avg, emotion_frequency, current_streak,
    best_day, worst_day, day_of_week_avg, day_scores.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    entries = (
        db_session.query(JournalEntry)
        .filter(JournalEntry.created_at >= cutoff)
        .order_by(JournalEntry.created_at.desc())
        .all()
    )
    entry_dicts = [e.to_dict() for e in entries]
    return calculate_trends(entry_dicts)


def calculate_trends(entries: list[dict]) -> dict:
    """Pure function: compute trend analytics from a list of entry dicts.

    Calculates: 7-day avg, 30-day avg, emotion frequency, positive mood
    streak, best/worst day, day-of-week patterns.
    """
    if not entries:
        return {
            "weekly_avg": 0.0,
            "monthly_avg": 0.0,
            "emotion_frequency": {},
            "current_streak": 0,
            "best_day": "",
            "worst_day": "",
            "day_of_week_avg": {},
            "day_scores": [],
        }

    scores = [e.get("mood_score", 0.0) for e in entries]
    dates = [e.get("created_at", "") for e in entries]

    # Rolling averages
    weekly = scores[:7] if len(scores) >= 7 else scores
    monthly = scores[:30] if len(scores) >= 30 else scores

    # Emotion frequency
    freq: Counter = Counter()
    for e in entries:
        emotions = e.get("emotions") or {}
        for emo, cnt in emotions.items():
            freq[emo] += cnt if isinstance(cnt, int) else 1

    # Positive mood streak (consecutive entries with score > 0)
    streak = 0
    for s in scores:
        if s > 0.0:
            streak += 1
        else:
            break

    # Best and worst days
    best_idx = scores.index(max(scores))
    worst_idx = scores.index(min(scores))
    best_day = dates[best_idx] if best_idx < len(dates) else ""
    worst_day = dates[worst_idx] if worst_idx < len(dates) else ""

    # Day-of-week average
    dow_scores: dict[str, list[float]] = {}
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday",
                 "Friday", "Saturday", "Sunday"]
    for e in entries:
        created = e.get("created_at", "")
        if created:
            try:
                dt = datetime.fromisoformat(created)
                day_name = day_names[dt.weekday()]
                dow_scores.setdefault(day_name, []).append(
                    e.get("mood_score", 0.0)
                )
            except (ValueError, IndexError):
                pass

    day_of_week_avg: dict[str, float] = {}
    for day, vals in dow_scores.items():
        day_of_week_avg[day] = round(sum(vals) / len(vals), 4) if vals else 0.0

    return {
        "weekly_avg": round(sum(weekly) / len(weekly), 4) if weekly else 0.0,
        "monthly_avg": round(sum(monthly) / len(monthly), 4) if monthly else 0.0,
        "emotion_frequency": dict(freq.most_common(10)),
        "current_streak": streak,
        "best_day": best_day,
        "worst_day": worst_day,
        "day_of_week_avg": day_of_week_avg,
        "day_scores": [
            {"index": i, "score": s, "date": dates[i] if i < len(dates) else ""}
            for i, s in enumerate(scores[:30])
        ],
    }


# ── Overall statistics ───────────────────────────────────────────────────


def get_stats(db_session) -> dict:
    """Return aggregate statistics across all entries."""
    total = db_session.query(JournalEntry).count()
    if total == 0:
        return {
            "total_entries": 0,
            "avg_mood": 0.0,
            "top_emotion": "neutral",
            "total_words": 0,
            "avg_words_per_entry": 0,
            "mood_distribution": {
                "very_positive": 0,
                "positive": 0,
                "neutral": 0,
                "negative": 0,
                "very_negative": 0,
            },
        }

    avg = db_session.query(func.avg(JournalEntry.mood_score)).scalar() or 0.0
    total_words = db_session.query(func.sum(JournalEntry.word_count)).scalar() or 0

    # Top emotion
    entries = db_session.query(JournalEntry).all()
    emo_counter: Counter = Counter()
    mood_dist: Counter = Counter()
    for e in entries:
        if e.dominant_emotion:
            emo_counter[e.dominant_emotion] += 1
        mood_dist[get_mood_label(e.mood_score)] += 1

    top = emo_counter.most_common(1)

    return {
        "total_entries": total,
        "avg_mood": round(float(avg), 4),
        "top_emotion": top[0][0] if top else "neutral",
        "total_words": int(total_words),
        "avg_words_per_entry": round(int(total_words) / total, 1),
        "mood_distribution": {
            "very_positive": mood_dist.get("very positive", 0),
            "positive": mood_dist.get("positive", 0),
            "neutral": mood_dist.get("neutral", 0),
            "negative": mood_dist.get("negative", 0),
            "very_negative": mood_dist.get("very negative", 0),
        },
    }


# ── Word frequencies ─────────────────────────────────────────────────────


def get_word_frequencies(db_session, limit: int = 50) -> dict:
    """Aggregate positive/negative word frequencies across all entries."""
    entries = (
        db_session.query(JournalEntry)
        .order_by(JournalEntry.created_at.desc())
        .limit(limit)
        .all()
    )
    pos_counter: Counter = Counter()
    neg_counter: Counter = Counter()

    for entry in entries:
        words = extract_sentiment_words(entry.content)
        for w, c in words["positive"].items():
            pos_counter[w] += c
        for w, c in words["negative"].items():
            neg_counter[w] += c

    return {
        "positive": dict(pos_counter.most_common(20)),
        "negative": dict(neg_counter.most_common(20)),
    }


# ── Wellness suggestions ─────────────────────────────────────────────────

WELLNESS_TIPS: dict[str, list[str]] = {
    "very_negative": [
        "Consider reaching out to a trusted friend or counsellor.",
        "Try a 5-minute breathing exercise to centre yourself.",
        "Journaling about three small things you are grateful for may help.",
        "A short walk outdoors can shift your perspective.",
    ],
    "negative": [
        "Take a few minutes for mindful breathing or meditation.",
        "Listen to music that makes you feel calm or uplifted.",
        "Write down one thing that went well today, however small.",
        "Spend a few minutes stretching or doing gentle yoga.",
    ],
    "neutral": [
        "Try setting a small, achievable goal for the rest of the day.",
        "Call or message someone you care about.",
        "Explore a new hobby or creative activity.",
        "Reflect on a happy memory and let yourself feel the warmth.",
    ],
    "positive": [
        "Keep the momentum going -- share your positivity with someone.",
        "Write a thank-you note to someone who made a difference.",
        "Use this energy to tackle a task you have been postponing.",
        "Savour this feeling and remember what contributed to it.",
    ],
    "very_positive": [
        "Wonderful! Consider journaling about why today was so great.",
        "Share your good mood -- compliment someone around you.",
        "Channel this energy into a creative project.",
        "Celebrate your wins, big and small.",
    ],
}


def get_wellness_suggestions(db_session) -> list[str]:
    """Generate suggestions based on recent mood patterns."""
    recent = (
        db_session.query(JournalEntry)
        .order_by(JournalEntry.created_at.desc())
        .limit(7)
        .all()
    )
    if not recent:
        return WELLNESS_TIPS["neutral"][:2]

    avg_score = sum(e.mood_score for e in recent) / len(recent)
    label = get_mood_label(avg_score).replace(" ", "_")
    tips = WELLNESS_TIPS.get(label, WELLNESS_TIPS["neutral"])

    # Pick 2-3 tips
    return tips[:3]


# ── Seed data ─────────────────────────────────────────────────────────────


def get_sample_entries() -> list[dict]:
    """Load sample journal entries from seed_data/data.json."""
    data_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "seed_data", "data.json",
    )
    if os.path.exists(data_path):
        with open(data_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def seed_database(db_session) -> int:
    """Seed the database with sample entries. Returns count of added rows."""
    existing = db_session.query(JournalEntry).count()
    if existing > 0:
        return 0

    samples = get_sample_entries()
    count = 0
    base_time = datetime.now(timezone.utc) - timedelta(days=len(samples))

    for i, sample in enumerate(samples):
        text = sample.get("content", "")
        analysis = analyze_sentiment(text)
        entry = JournalEntry(
            content=text,
            mood_score=analysis["mood_score"],
            mood_label=analysis.get("mood_label", "neutral"),
            dominant_emotion=analysis["dominant_emotion"],
            emotions=analysis.get("emotion_breakdown", {}),
            word_count=analysis["word_count"],
            positive_count=analysis.get("positive_word_count", 0),
            negative_count=analysis.get("negative_word_count", 0),
            created_at=base_time + timedelta(days=i, hours=i % 12),
        )
        db_session.add(entry)
        count += 1

    db_session.commit()
    return count
