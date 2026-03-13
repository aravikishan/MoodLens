"""SQLAlchemy models and Pydantic schemas for MoodLens."""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field
from models.database import db


# ── SQLAlchemy ORM models ─────────────────────────────────────────────────


class JournalEntry(db.Model):
    """A single mood journal entry written by the user."""

    __tablename__ = "journal_entries"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.Text, nullable=False)
    mood_score = db.Column(db.Float, nullable=False, default=0.0)
    mood_label = db.Column(db.String(30), nullable=False, default="neutral")
    dominant_emotion = db.Column(db.String(50), nullable=False, default="neutral")
    emotions = db.Column(db.JSON, nullable=True)
    word_count = db.Column(db.Integer, nullable=False, default=0)
    positive_count = db.Column(db.Integer, nullable=False, default=0)
    negative_count = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self):
        """Serialize entry to a plain dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "mood_score": self.mood_score,
            "mood_label": self.mood_label,
            "dominant_emotion": self.dominant_emotion,
            "emotions": self.emotions or {},
            "word_count": self.word_count,
            "positive_count": self.positive_count,
            "negative_count": self.negative_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class MoodRecord(db.Model):
    """Daily mood summary for trend tracking."""

    __tablename__ = "mood_records"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    avg_mood = db.Column(db.Float, nullable=False, default=0.0)
    entry_count = db.Column(db.Integer, nullable=False, default=0)
    top_emotion = db.Column(db.String(50), nullable=True)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self):
        """Serialize record to a plain dictionary."""
        return {
            "id": self.id,
            "date": self.date.isoformat() if self.date else None,
            "avg_mood": self.avg_mood,
            "entry_count": self.entry_count,
            "top_emotion": self.top_emotion,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ── Pydantic validation schemas ──────────────────────────────────────────


class EntryInput(BaseModel):
    """Validation schema for creating a journal entry."""

    content: str = Field(..., min_length=1, max_length=5000)


class EntryResponse(BaseModel):
    """Response schema for a journal entry."""

    id: int
    content: str
    mood_score: float
    mood_label: str = "neutral"
    dominant_emotion: str
    emotions: dict = Field(default_factory=dict)
    word_count: int
    positive_count: int = 0
    negative_count: int = 0
    created_at: Optional[str] = None


class AnalysisResult(BaseModel):
    """Schema for a standalone sentiment analysis result."""

    mood_score: float = 0.0
    mood_label: str = "neutral"
    dominant_emotion: str = "neutral"
    emotion_breakdown: dict = Field(default_factory=dict)
    emotion_confidence: dict = Field(default_factory=dict)
    word_count: int = 0
    positive_word_count: int = 0
    negative_word_count: int = 0
    mood_color: str = "#eab308"


class TrendData(BaseModel):
    """Schema for mood trend analytics."""

    dates: list[str] = Field(default_factory=list)
    scores: list[float] = Field(default_factory=list)
    emotions: dict = Field(default_factory=dict)
    weekly_avg: float = 0.0
    monthly_avg: float = 0.0
    total_entries: int = 0
    current_streak: int = 0
    best_day: str = ""
    worst_day: str = ""
    day_of_week_avg: dict = Field(default_factory=dict)
    top_emotion: str = "neutral"
