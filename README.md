# MoodLens

> A mood journaling application with lexicon-based sentiment analysis, emotion
> tracking, and wellness trend analytics.

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Tests](https://img.shields.io/badge/Tests-15%20passing-22c55e)
![Coverage](https://img.shields.io/badge/Coverage-90%25-22c55e)

---

## Overview

MoodLens helps you understand your emotional well-being through daily
journaling.  Write about your day and receive **instant mood analysis** powered
by a curated lexicon-based sentiment engine -- no external AI APIs required.

### Key Features

| Feature | Description |
|---------|-------------|
| Mood Journaling | Write free-form entries with optional emoji mood picker |
| Sentiment Analysis | 120+ word lexicon with weighted positive/negative scoring |
| Emotion Detection | Seven categories: joy, sadness, anger, fear, love, surprise, calm |
| Trend Analytics | 7-day / 30-day rolling averages, mood streaks, day-of-week patterns |
| Wellness Insights | Personalised suggestions based on recent mood patterns |
| Word Cloud | See your most frequent positive and negative words |
| Search & Filter | Find past entries by keyword, date range, or emotion |
| REST API | Full CRUD plus analysis endpoints for programmatic access |
| Dashboard | Mood distribution chart, trend line, recent entries at a glance |

---

## Architecture

```
MoodLens/
+-- app.py                      # Flask entry point & factory
+-- config.py                   # App configuration constants
+-- models/
|   +-- __init__.py
|   +-- database.py             # SQLAlchemy setup, init_db()
|   +-- schemas.py              # JournalEntry, MoodRecord models
+-- routes/
|   +-- __init__.py
|   +-- api.py                  # REST API endpoints
|   +-- views.py                # HTML-serving page routes
+-- services/
|   +-- __init__.py
|   +-- sentiment.py            # Lexicon-based sentiment engine
|   +-- analytics.py            # Trend computation, mood statistics
+-- templates/
|   +-- base.html               # Shared layout with nav
|   +-- index.html              # Dashboard with mood overview
|   +-- journal.html            # Write new journal entry
|   +-- entries.html            # Browse past entries
|   +-- analytics.html          # Trend charts and insights
|   +-- about.html              # About page
+-- static/
|   +-- css/style.css           # Calming pastel wellness theme
|   +-- js/main.js              # Charts, mood picker, real-time sentiment
+-- tests/
|   +-- conftest.py             # Shared pytest fixtures
|   +-- test_api.py             # API endpoint tests
|   +-- test_models.py          # Model / schema tests
|   +-- test_services.py        # Sentiment & analytics tests
+-- seed_data/data.json         # 20 sample journal entries
+-- Dockerfile
+-- docker-compose.yml
+-- start.sh
+-- requirements.txt
+-- LICENSE
+-- .gitignore
+-- .github/workflows/ci.yml
```

---

## Getting Started

### Prerequisites

- Python 3.11 or higher
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/ravikishan/MoodLens.git
cd MoodLens

# Create a virtual environment
python -m venv venv
source venv/bin/activate       # Linux / macOS
# venv\Scripts\activate       # Windows

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

The app will be available at [http://localhost:8008](http://localhost:8008).

### Docker

```bash
docker compose up --build
```

---

## API Reference

All endpoints return JSON.

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/entries` | Create a journal entry with sentiment analysis |
| `GET`  | `/api/entries` | List entries (`?limit=`, `?offset=`, `?search=`) |
| `GET`  | `/api/entries/<id>` | Get a single entry by ID |
| `DELETE` | `/api/entries/<id>` | Delete a single entry |
| `POST` | `/api/analyze` | Analyze text without saving |
| `GET`  | `/api/trends` | Mood trends (`?days=30`) |
| `GET`  | `/api/stats` | Overall statistics |
| `GET`  | `/api/word-cloud` | Positive and negative word frequencies |
| `GET`  | `/api/suggestions` | Wellness suggestions based on recent mood |
| `GET`  | `/api/health` | Health check |

### Example: Create Entry

```bash
curl -X POST http://localhost:8008/api/entries \
  -H "Content-Type: application/json" \
  -d '{"content": "Today was a wonderful day full of joy and gratitude!"}'
```

Response:

```json
{
  "entry": {
    "id": 1,
    "content": "Today was a wonderful day full of joy and gratitude!",
    "mood_score": 0.64,
    "dominant_emotion": "joy",
    "emotions": {"joy": 2, "love": 1},
    "word_count": 10,
    "created_at": "2024-01-15T10:30:00"
  },
  "analysis": {
    "mood_score": 0.64,
    "mood_label": "very positive",
    "dominant_emotion": "joy",
    "emotion_breakdown": {"joy": 2, "love": 1},
    "word_count": 10,
    "positive_word_count": 3,
    "negative_word_count": 0,
    "mood_color": "#16a34a"
  }
}
```

### Example: Analyze Without Saving

```bash
curl -X POST http://localhost:8008/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"content": "I feel anxious and worried about the future."}'
```

---

## Sentiment Analysis Engine

MoodLens uses a **lexicon-based** approach -- zero external API calls:

1. **Tokenization** -- lowercase, strip punctuation, split into words
2. **Scoring** -- each word matched against positive (60+ words, 0.5--1.0)
   and negative (60+ words, -0.5 to -1.0) lexicons
3. **Normalisation** -- aggregate score clamped to \[-1.0, 1.0\]
4. **Emotion Detection** -- words matched against 7 emotion categories
   (joy, sadness, anger, fear, love, surprise, calm) with confidence scores
5. **Labels** -- score mapped to: very negative, negative, neutral,
   positive, very positive

---

## Pages

| Route | Page | Description |
|-------|------|-------------|
| `/` | Dashboard | Mood overview with recent entries and distribution |
| `/journal` | Journal | Write new entries with emoji picker |
| `/entries` | Entries | Browse and search past entries |
| `/analytics` | Analytics | Trend charts, emotion frequency, insights |
| `/about` | About | About MoodLens and how it works |

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage report
pytest tests/ -v --cov=. --cov-report=term-missing

# Individual test files
pytest tests/test_services.py -v
pytest tests/test_api.py -v
pytest tests/test_models.py -v
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8008` | Server port |
| `SECRET_KEY` | `moodlens-dev-secret-key` | Flask secret key |
| `DATABASE_URL` | `sqlite:///instance/moodlens.db` | Database URL |
| `FLASK_DEBUG` | `0` | Enable debug mode (`1` to enable) |

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for
details.

---

## Author

**ravikishan** -- [GitHub](https://github.com/ravikishan)
