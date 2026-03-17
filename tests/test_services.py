"""Sentiment analysis and analytics service tests for MoodLens."""

from services.sentiment import (
    analyze_sentiment,
    extract_sentiment_words,
    get_mood_color,
    get_mood_emoji,
    get_mood_label,
)
from services.analytics import calculate_trends


def test_positive_sentiment():
    """Positive text should produce a positive mood score."""
    result = analyze_sentiment(
        "I am so happy and grateful, this is a wonderful amazing day!"
    )
    assert result["mood_score"] > 0
    assert result["mood_label"] in ("positive", "very positive")
    assert result["positive_word_count"] > 0


def test_negative_sentiment():
    """Negative text should produce a negative mood score."""
    result = analyze_sentiment(
        "I feel sad and frustrated, everything is terrible and hopeless."
    )
    assert result["mood_score"] < 0
    assert result["mood_label"] in ("negative", "very negative")
    assert result["negative_word_count"] > 0


def test_neutral_text():
    """Neutral text with no sentiment words should score near zero."""
    result = analyze_sentiment("The meeting is at three in the room.")
    assert -0.3 <= result["mood_score"] <= 0.3
    assert result["mood_label"] == "neutral"


def test_empty_text():
    """Empty text should return neutral defaults."""
    result = analyze_sentiment("")
    assert result["mood_score"] == 0.0
    assert result["word_count"] == 0


def test_emotion_detection_fear():
    """Fear keywords should be detected correctly."""
    result = analyze_sentiment(
        "I am so scared and anxious about tomorrow, terrified."
    )
    assert "fear" in result["emotion_breakdown"]
    assert result["dominant_emotion"] == "fear"


def test_emotion_detection_joy():
    """Joy keywords should be detected."""
    result = analyze_sentiment("I am happy and excited and delighted today!")
    assert "joy" in result["emotion_breakdown"]


def test_emotion_confidence():
    """Emotion confidence scores should sum close to 1.0."""
    result = analyze_sentiment("I am happy but also a bit worried and scared.")
    confidence = result.get("emotion_confidence", {})
    if confidence:
        total = sum(confidence.values())
        assert 0.99 <= total <= 1.01


def test_mood_label():
    """get_mood_label returns correct labels for each range."""
    assert get_mood_label(-0.8) == "very negative"
    assert get_mood_label(-0.4) == "negative"
    assert get_mood_label(0.0) == "neutral"
    assert get_mood_label(0.4) == "positive"
    assert get_mood_label(0.8) == "very positive"


def test_mood_color():
    """get_mood_color returns appropriate hex colours."""
    assert get_mood_color(-0.8) == "#ef4444"
    assert get_mood_color(0.0) == "#eab308"
    assert get_mood_color(0.8) == "#16a34a"


def test_mood_emoji():
    """get_mood_emoji returns appropriate emoji strings."""
    assert isinstance(get_mood_emoji(-0.8), str)
    assert isinstance(get_mood_emoji(0.0), str)
    assert isinstance(get_mood_emoji(0.8), str)


def test_extract_sentiment_words():
    """extract_sentiment_words identifies positive and negative words."""
    words = extract_sentiment_words("I am happy but also sad and frustrated.")
    assert "happy" in words["positive"]
    assert "sad" in words["negative"]


def test_trend_calculation():
    """calculate_trends produces correct summaries."""
    entries = [
        {"mood_score": 0.5, "emotions": {"joy": 2},
         "created_at": "2024-01-03T10:00:00"},
        {"mood_score": 0.3, "emotions": {"joy": 1, "calm": 1},
         "created_at": "2024-01-02T10:00:00"},
        {"mood_score": -0.2, "emotions": {"sadness": 1},
         "created_at": "2024-01-01T10:00:00"},
    ]
    result = calculate_trends(entries)
    assert "weekly_avg" in result
    assert "monthly_avg" in result
    assert "emotion_frequency" in result
    assert "day_of_week_avg" in result
    assert result["current_streak"] == 2  # first two are positive


def test_trend_empty():
    """calculate_trends with empty list returns safe defaults."""
    result = calculate_trends([])
    assert result["weekly_avg"] == 0.0
    assert result["current_streak"] == 0
    assert result["best_day"] == ""


def test_trend_best_worst_day():
    """calculate_trends identifies best and worst days."""
    entries = [
        {"mood_score": 0.9, "emotions": {}, "created_at": "2024-01-03T10:00:00"},
        {"mood_score": -0.5, "emotions": {}, "created_at": "2024-01-02T10:00:00"},
    ]
    result = calculate_trends(entries)
    assert result["best_day"] == "2024-01-03T10:00:00"
    assert result["worst_day"] == "2024-01-02T10:00:00"
