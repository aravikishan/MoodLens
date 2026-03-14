"""Text sentiment analysis engine for MoodLens.

Uses a curated lexicon-based approach -- no external APIs.  Sentiment is
computed from word-level scores against positive/negative word lists, and
emotions are detected via keyword matching with confidence scoring.
"""

import re
import string
from collections import Counter

# ── Positive word lexicon (word -> weight 0.0 to 1.0) ────────────────────

POSITIVE_WORDS: dict[str, float] = {
    "happy": 0.8, "joy": 0.9, "love": 0.9, "excited": 0.85,
    "grateful": 0.9, "wonderful": 0.85, "amazing": 0.85, "great": 0.7,
    "fantastic": 0.9, "blessed": 0.85, "peaceful": 0.8, "hopeful": 0.75,
    "confident": 0.7, "proud": 0.75, "inspired": 0.8, "delighted": 0.85,
    "cheerful": 0.8, "optimistic": 0.75, "content": 0.7, "thrilled": 0.9,
    "elated": 0.9, "ecstatic": 0.95, "blissful": 0.9, "radiant": 0.8,
    "vibrant": 0.7, "energetic": 0.65, "motivated": 0.7,
    "enthusiastic": 0.8, "passionate": 0.75, "caring": 0.7, "kind": 0.65,
    "generous": 0.7, "compassionate": 0.75, "empathetic": 0.7,
    "warm": 0.6, "gentle": 0.6, "calm": 0.65, "relaxed": 0.65,
    "serene": 0.75, "tranquil": 0.7, "harmonious": 0.7, "balanced": 0.6,
    "fulfilled": 0.8, "accomplished": 0.75, "successful": 0.7,
    "creative": 0.65, "imaginative": 0.6, "playful": 0.65,
    "adventurous": 0.7, "courageous": 0.7, "brave": 0.7, "strong": 0.6,
    "resilient": 0.7, "determined": 0.65, "focused": 0.6, "mindful": 0.65,
    "appreciative": 0.75, "thankful": 0.8, "beautiful": 0.7,
    "awesome": 0.75, "excellent": 0.8, "good": 0.5, "nice": 0.5,
    "fine": 0.4, "pleasant": 0.6, "joyful": 0.85, "overjoyed": 0.9,
    "euphoric": 0.95, "laughter": 0.75, "smile": 0.65, "fun": 0.65,
}

# ── Negative word lexicon (word -> weight -1.0 to 0.0) ───────────────────

NEGATIVE_WORDS: dict[str, float] = {
    "sad": -0.8, "angry": -0.85, "frustrated": -0.7, "anxious": -0.75,
    "worried": -0.7, "depressed": -0.95, "lonely": -0.8,
    "stressed": -0.75, "overwhelmed": -0.8, "hurt": -0.8,
    "disappointed": -0.7, "exhausted": -0.7, "fearful": -0.8,
    "irritated": -0.65, "hopeless": -0.95, "miserable": -0.9,
    "devastated": -0.95, "heartbroken": -0.9, "anguished": -0.85,
    "despair": -0.95, "grief": -0.9, "sorrowful": -0.85,
    "melancholy": -0.75, "gloomy": -0.7, "bitter": -0.7,
    "resentful": -0.75, "jealous": -0.65, "envious": -0.6,
    "guilty": -0.7, "ashamed": -0.75, "embarrassed": -0.6,
    "insecure": -0.65, "nervous": -0.6, "panic": -0.85,
    "terrified": -0.9, "horrified": -0.85, "disgusted": -0.7,
    "contempt": -0.7, "hostile": -0.8, "furious": -0.9,
    "outraged": -0.85, "annoyed": -0.55, "bored": -0.5,
    "apathetic": -0.6, "numb": -0.65, "empty": -0.75, "lost": -0.7,
    "confused": -0.55, "helpless": -0.8, "powerless": -0.8,
    "trapped": -0.85, "suffocated": -0.85, "drained": -0.7,
    "burned": -0.65, "broken": -0.85, "shattered": -0.9,
    "crying": -0.75, "tearful": -0.7, "bad": -0.6, "terrible": -0.8,
    "awful": -0.8, "horrible": -0.85, "worst": -0.9, "hate": -0.85,
    "scared": -0.75, "dread": -0.8, "unhappy": -0.75, "pain": -0.7,
}

# ── Emotion keyword map ──────────────────────────────────────────────────

EMOTION_KEYWORDS: dict[str, list[str]] = {
    "joy": [
        "happy", "excited", "delighted", "cheerful", "elated", "ecstatic",
        "blissful", "thrilled", "radiant", "jubilant", "merry", "glad",
        "joyful", "overjoyed", "euphoric", "fun", "laughter", "smile",
    ],
    "sadness": [
        "sad", "crying", "tearful", "heartbroken", "melancholy", "grief",
        "sorrowful", "depressed", "gloomy", "miserable", "devastated",
        "lonely", "despair", "mourn", "unhappy", "down", "blue",
    ],
    "anger": [
        "angry", "furious", "irritated", "annoyed", "outraged", "hostile",
        "bitter", "resentful", "frustrated", "enraged", "livid", "mad",
        "aggravated", "infuriated", "irate", "seething",
    ],
    "fear": [
        "scared", "anxious", "worried", "terrified", "nervous", "panic",
        "fearful", "horrified", "dread", "uneasy", "apprehensive",
        "frightened", "alarmed", "phobia", "tense", "overwhelmed",
    ],
    "love": [
        "love", "adore", "cherish", "affection", "caring", "devoted",
        "passionate", "tender", "warmth", "embrace", "compassion",
        "romantic", "intimate", "fond", "attachment", "dear",
    ],
    "surprise": [
        "surprised", "amazed", "astonished", "shocked", "stunned",
        "speechless", "unexpected", "startled", "bewildered",
        "flabbergasted", "awestruck", "disbelief", "wonder",
    ],
    "calm": [
        "peaceful", "relaxed", "serene", "tranquil", "zen", "still",
        "quiet", "composed", "centered", "balanced", "mindful",
        "meditative", "soothing", "gentle", "harmonious", "mellow",
    ],
}

# Pre-compute a flat set for quick membership tests
_ALL_EMOTION_WORDS: set[str] = set()
for _words in EMOTION_KEYWORDS.values():
    _ALL_EMOTION_WORDS.update(_words)


# ── Negation handling ────────────────────────────────────────────────────

NEGATION_WORDS = frozenset([
    "not", "no", "never", "neither", "nobody", "nothing", "nowhere",
    "nor", "cannot", "without", "hardly", "barely", "scarcely",
])

INTENSIFIERS: dict[str, float] = {
    "very": 1.3, "really": 1.3, "extremely": 1.5, "incredibly": 1.5,
    "absolutely": 1.5, "truly": 1.2, "deeply": 1.3, "so": 1.2,
    "quite": 1.1, "rather": 1.1, "totally": 1.4, "utterly": 1.4,
}


def _tokenize(text: str) -> list[str]:
    """Lowercase, strip punctuation, split into word tokens."""
    text = text.lower()
    text = re.sub(f"[{re.escape(string.punctuation)}]", " ", text)
    return [w.strip() for w in text.split() if w.strip()]


def analyze_sentiment(text: str) -> dict:
    """Analyse text and return mood score, label, emotions, word info.

    Returns dict with keys:
        mood_score, mood_label, dominant_emotion, emotion_breakdown,
        emotion_confidence, word_count, positive_word_count,
        negative_word_count
    """
    tokens = _tokenize(text)
    word_count = len(tokens)

    if word_count == 0:
        return {
            "mood_score": 0.0,
            "mood_label": "neutral",
            "dominant_emotion": "neutral",
            "emotion_breakdown": {},
            "emotion_confidence": {},
            "word_count": 0,
            "positive_word_count": 0,
            "negative_word_count": 0,
        }

    # ── Score individual words with negation and intensifier handling ──
    positive_score = 0.0
    negative_score = 0.0
    positive_count = 0
    negative_count = 0
    is_negated = False
    intensifier = 1.0

    for i, token in enumerate(tokens):
        # Check for negation
        if token in NEGATION_WORDS:
            is_negated = True
            continue

        # Check for intensifier
        if token in INTENSIFIERS:
            intensifier = INTENSIFIERS[token]
            continue

        # Score the token
        if token in POSITIVE_WORDS:
            weight = POSITIVE_WORDS[token] * intensifier
            if is_negated:
                negative_score -= weight * 0.5
                negative_count += 1
            else:
                positive_score += weight
                positive_count += 1

        if token in NEGATIVE_WORDS:
            weight = NEGATIVE_WORDS[token] * intensifier
            if is_negated:
                positive_score += abs(weight) * 0.5
                positive_count += 1
            else:
                negative_score += weight
                negative_count += 1

        # Reset modifiers after use
        is_negated = False
        intensifier = 1.0

    # Overall mood score clamped to [-1, 1]
    raw = (positive_score + negative_score) / max(word_count, 1)
    mood_score = round(max(-1.0, min(1.0, raw * 3)), 4)

    # ── Detect emotions with confidence scoring ──
    emotion_counts: dict[str, int] = {}
    for emotion, keywords in EMOTION_KEYWORDS.items():
        count = sum(1 for t in tokens if t in keywords)
        if count > 0:
            emotion_counts[emotion] = count

    # Confidence: emotion count / total emotion-bearing words
    total_emotion_hits = sum(emotion_counts.values()) if emotion_counts else 1
    emotion_confidence: dict[str, float] = {}
    for emo, cnt in emotion_counts.items():
        emotion_confidence[emo] = round(cnt / total_emotion_hits, 3)

    dominant_emotion = (
        max(emotion_counts, key=emotion_counts.get)
        if emotion_counts
        else "neutral"
    )

    return {
        "mood_score": mood_score,
        "mood_label": get_mood_label(mood_score),
        "dominant_emotion": dominant_emotion,
        "emotion_breakdown": emotion_counts,
        "emotion_confidence": emotion_confidence,
        "word_count": word_count,
        "positive_word_count": positive_count,
        "negative_word_count": negative_count,
    }


def get_mood_label(score: float) -> str:
    """Map a mood score to a human-readable label."""
    if score <= -0.6:
        return "very negative"
    if score <= -0.2:
        return "negative"
    if score <= 0.2:
        return "neutral"
    if score <= 0.6:
        return "positive"
    return "very positive"


def get_mood_color(score: float) -> str:
    """Return a hex colour string representing the mood score."""
    if score <= -0.6:
        return "#ef4444"
    if score <= -0.2:
        return "#f97316"
    if score <= 0.2:
        return "#eab308"
    if score <= 0.6:
        return "#22c55e"
    return "#16a34a"


def get_mood_emoji(score: float) -> str:
    """Return an emoji representing the mood score."""
    if score <= -0.6:
        return "😢"
    if score <= -0.2:
        return "😟"
    if score <= 0.2:
        return "😐"
    if score <= 0.6:
        return "🙂"
    return "😊"


def extract_sentiment_words(text: str) -> dict:
    """Extract positive and negative words found in the text."""
    tokens = _tokenize(text)
    positive_found = [t for t in tokens if t in POSITIVE_WORDS]
    negative_found = [t for t in tokens if t in NEGATIVE_WORDS]
    return {
        "positive": dict(Counter(positive_found).most_common(20)),
        "negative": dict(Counter(negative_found).most_common(20)),
    }
