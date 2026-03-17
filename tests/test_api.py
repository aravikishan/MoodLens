"""API endpoint tests for MoodLens."""

import json


def test_health(client):
    """Health endpoint returns healthy status."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "healthy"
    assert data["service"] == "MoodLens"


def test_create_entry(client):
    """POST /api/entries creates an entry with analysis."""
    resp = client.post(
        "/api/entries",
        data=json.dumps({"content": "I am feeling very happy and grateful today!"}),
        content_type="application/json",
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert "entry" in data
    assert "analysis" in data
    assert data["analysis"]["mood_score"] > 0
    assert data["entry"]["word_count"] > 0


def test_create_entry_empty(client):
    """POST /api/entries with empty content returns 400."""
    resp = client.post(
        "/api/entries",
        data=json.dumps({"content": ""}),
        content_type="application/json",
    )
    assert resp.status_code == 400


def test_create_entry_no_body(client):
    """POST /api/entries with no JSON body returns 400."""
    resp = client.post("/api/entries", content_type="application/json")
    assert resp.status_code == 400


def test_list_entries(client):
    """GET /api/entries returns entries list."""
    client.post(
        "/api/entries",
        data=json.dumps({"content": "Today was a wonderful day."}),
        content_type="application/json",
    )
    resp = client.get("/api/entries")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "entries" in data
    assert len(data["entries"]) >= 1


def test_get_single_entry(client):
    """GET /api/entries/<id> returns a single entry."""
    post_resp = client.post(
        "/api/entries",
        data=json.dumps({"content": "Feeling great about this test."}),
        content_type="application/json",
    )
    entry_id = post_resp.get_json()["entry"]["id"]
    resp = client.get(f"/api/entries/{entry_id}")
    assert resp.status_code == 200
    assert resp.get_json()["entry"]["id"] == entry_id


def test_get_entry_not_found(client):
    """GET /api/entries/99999 returns 404."""
    resp = client.get("/api/entries/99999")
    assert resp.status_code == 404


def test_delete_entry(client):
    """DELETE /api/entries/<id> removes the entry."""
    post_resp = client.post(
        "/api/entries",
        data=json.dumps({"content": "Entry to be deleted."}),
        content_type="application/json",
    )
    entry_id = post_resp.get_json()["entry"]["id"]
    resp = client.delete(f"/api/entries/{entry_id}")
    assert resp.status_code == 200
    assert resp.get_json()["id"] == entry_id
    # Verify it is gone
    resp2 = client.get(f"/api/entries/{entry_id}")
    assert resp2.status_code == 404


def test_analyze_without_saving(client):
    """POST /api/analyze returns analysis without saving."""
    resp = client.post(
        "/api/analyze",
        data=json.dumps({"content": "I am excited and thrilled!"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert "analysis" in data
    assert data["analysis"]["mood_score"] > 0
    # Verify nothing was saved
    entries_resp = client.get("/api/entries")
    assert entries_resp.get_json()["count"] == 0


def test_search_entries(client):
    """GET /api/entries?search= filters by keyword."""
    client.post(
        "/api/entries",
        data=json.dumps({"content": "The sunshine made me happy today."}),
        content_type="application/json",
    )
    client.post(
        "/api/entries",
        data=json.dumps({"content": "Rainy day, feeling gloomy."}),
        content_type="application/json",
    )
    resp = client.get("/api/entries?search=sunshine")
    data = resp.get_json()
    assert len(data["entries"]) == 1
    assert "sunshine" in data["entries"][0]["content"]


def test_trends(client):
    """GET /api/trends returns trend data."""
    client.post(
        "/api/entries",
        data=json.dumps({"content": "I love this amazing day!"}),
        content_type="application/json",
    )
    resp = client.get("/api/trends?days=7")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "trends" in data


def test_stats(client):
    """GET /api/stats returns statistics."""
    client.post(
        "/api/entries",
        data=json.dumps({"content": "Feeling peaceful and calm."}),
        content_type="application/json",
    )
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "stats" in data
    assert data["stats"]["total_entries"] >= 1


def test_word_cloud(client):
    """GET /api/word-cloud returns word frequencies."""
    client.post(
        "/api/entries",
        data=json.dumps({"content": "Happy happy joy joy wonderful day!"}),
        content_type="application/json",
    )
    resp = client.get("/api/word-cloud")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "words" in data
    assert "positive" in data["words"]


def test_suggestions(client):
    """GET /api/suggestions returns wellness tips."""
    client.post(
        "/api/entries",
        data=json.dumps({"content": "I feel great and happy and wonderful!"}),
        content_type="application/json",
    )
    resp = client.get("/api/suggestions")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "suggestions" in data
    assert len(data["suggestions"]) > 0
