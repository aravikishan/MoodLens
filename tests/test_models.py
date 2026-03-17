"""Model and schema tests for MoodLens."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError


def test_journal_entry_creation(db_session):
    """JournalEntry can be created and persisted."""
    from models.schemas import JournalEntry

    entry = JournalEntry(
        content="Test entry for model test",
        mood_score=0.5,
        mood_label="positive",
        dominant_emotion="joy",
        emotions={"joy": 2},
        word_count=5,
        positive_count=2,
        negative_count=0,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(entry)
    db_session.commit()

    fetched = db_session.get(JournalEntry, entry.id)
    assert fetched is not None
    assert fetched.content == "Test entry for model test"
    assert fetched.mood_score == 0.5
    assert fetched.dominant_emotion == "joy"
    assert fetched.mood_label == "positive"


def test_journal_entry_to_dict(db_session):
    """to_dict serialises all fields correctly."""
    from models.schemas import JournalEntry

    entry = JournalEntry(
        content="Hello world",
        mood_score=-0.3,
        mood_label="negative",
        dominant_emotion="sadness",
        emotions={"sadness": 1},
        word_count=2,
        positive_count=0,
        negative_count=1,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(entry)
    db_session.commit()

    d = entry.to_dict()
    assert d["content"] == "Hello world"
    assert d["mood_score"] == -0.3
    assert d["mood_label"] == "negative"
    assert "created_at" in d


def test_mood_record_creation(db_session):
    """MoodRecord can be created and persisted."""
    from models.schemas import MoodRecord

    record = MoodRecord(
        date=datetime.now(timezone.utc).date(),
        avg_mood=0.65,
        entry_count=5,
        top_emotion="joy",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(record)
    db_session.commit()

    fetched = db_session.get(MoodRecord, record.id)
    assert fetched is not None
    assert fetched.avg_mood == 0.65
    assert fetched.entry_count == 5


def test_entry_input_validation():
    """EntryInput requires non-empty content."""
    from models.schemas import EntryInput

    entry = EntryInput(content="Hello")
    assert entry.content == "Hello"

    with pytest.raises(ValidationError):
        EntryInput(content="")


def test_entry_response_schema():
    """EntryResponse accepts valid data."""
    from models.schemas import EntryResponse

    resp = EntryResponse(
        id=1,
        content="Test",
        mood_score=0.5,
        mood_label="positive",
        dominant_emotion="joy",
        emotions={"joy": 1},
        word_count=1,
        positive_count=1,
        negative_count=0,
        created_at="2024-01-01T00:00:00",
    )
    assert resp.id == 1
    assert resp.mood_score == 0.5


def test_analysis_result_schema():
    """AnalysisResult has correct defaults."""
    from models.schemas import AnalysisResult

    ar = AnalysisResult()
    assert ar.mood_score == 0.0
    assert ar.mood_label == "neutral"
    assert ar.mood_color == "#eab308"


def test_trend_data_schema():
    """TrendData has correct defaults."""
    from models.schemas import TrendData

    td = TrendData()
    assert td.dates == []
    assert td.weekly_avg == 0.0
    assert td.monthly_avg == 0.0
    assert td.top_emotion == "neutral"
