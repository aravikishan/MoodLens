/* MoodLens frontend logic -- charts, mood picker, API calls */

/* ── Utility ──────────────────────────────────────────────────────────── */

function moodColor(score) {
    if (score <= -0.6) return '#ef4444';
    if (score <= -0.2) return '#f97316';
    if (score <= 0.2)  return '#eab308';
    if (score <= 0.6)  return '#22c55e';
    return '#16a34a';
}

function moodLabel(score) {
    if (score <= -0.6) return 'very negative';
    if (score <= -0.2) return 'negative';
    if (score <= 0.2)  return 'neutral';
    if (score <= 0.6)  return 'positive';
    return 'very positive';
}

function escapeHtml(t) {
    var d = document.createElement('div');
    d.textContent = t;
    return d.innerHTML;
}

function formatDate(iso) {
    if (!iso) return '--';
    return new Date(iso).toLocaleDateString('en-US', {
        year: 'numeric', month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit'
    });
}

/* ── Save journal entry ───────────────────────────────────────────────── */

function saveEntry() {
    var input = document.getElementById('journal-input');
    var content = input.value.trim();
    if (!content) { alert('Please write something first.'); return; }

    var btn = document.getElementById('save-btn');
    btn.disabled = true;
    btn.textContent = 'Saving...';

    fetch('/api/entries', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: content })
    })
    .then(function(res) { return res.json(); })
    .then(function(data) {
        btn.disabled = false;
        btn.textContent = 'Save Entry';
        if (data.error) { alert(data.error); return; }
        showSavedAnalysis(data.analysis);
        input.value = '';
        document.getElementById('char-count').textContent = '0 / 5000';
        // Hide preview if visible
        var preview = document.getElementById('sentiment-preview');
        if (preview) preview.style.display = 'none';
    })
    .catch(function(err) {
        btn.disabled = false;
        btn.textContent = 'Save Entry';
        alert('Error saving entry.');
        console.error(err);
    });
}

function showSavedAnalysis(a) {
    var section = document.getElementById('analysis-result');
    if (!section) return;
    section.style.display = 'block';

    var scoreEl = document.getElementById('result-score');
    scoreEl.textContent = a.mood_score.toFixed(2);
    scoreEl.style.background = moodColor(a.mood_score);

    document.getElementById('result-label').textContent = a.mood_label;
    document.getElementById('result-emotion').textContent = a.dominant_emotion;
    document.getElementById('result-words').textContent = a.word_count;

    var bd = document.getElementById('emotion-breakdown');
    if (bd) {
        bd.innerHTML = '';
        var emo = a.emotion_breakdown || {};
        for (var key in emo) {
            var tag = document.createElement('span');
            tag.className = 'emo-tag';
            tag.textContent = key + ': ' + emo[key];
            bd.appendChild(tag);
        }
    }
    section.scrollIntoView({ behavior: 'smooth' });
}

/* ── Preview sentiment (real-time analysis without saving) ────────────── */

function previewSentiment() {
    var input = document.getElementById('journal-input');
    var content = input.value.trim();
    if (!content) { alert('Please write something first.'); return; }

    var btn = document.getElementById('preview-btn');
    btn.disabled = true;
    btn.textContent = 'Analysing...';

    fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: content })
    })
    .then(function(res) { return res.json(); })
    .then(function(data) {
        btn.disabled = false;
        btn.textContent = 'Preview Mood';
        if (data.error) { alert(data.error); return; }
        showPreview(data.analysis);
    })
    .catch(function(err) {
        btn.disabled = false;
        btn.textContent = 'Preview Mood';
        console.error(err);
    });
}

function showPreview(a) {
    var section = document.getElementById('sentiment-preview');
    if (!section) return;
    section.style.display = 'block';

    var scoreEl = document.getElementById('preview-score');
    scoreEl.textContent = a.mood_score.toFixed(2);
    scoreEl.style.background = moodColor(a.mood_score);

    document.getElementById('preview-label').textContent = a.mood_label;
    document.getElementById('preview-emotion').textContent = a.dominant_emotion;
    document.getElementById('preview-words').textContent = a.word_count;

    // Emotion breakdown
    var bd = document.getElementById('preview-emotions');
    if (bd) {
        bd.innerHTML = '';
        var emo = a.emotion_breakdown || {};
        for (var key in emo) {
            var tag = document.createElement('span');
            tag.className = 'emo-tag';
            tag.textContent = key + ': ' + emo[key];
            bd.appendChild(tag);
        }
    }

    // Confidence
    var conf = document.getElementById('preview-confidence');
    if (conf) {
        conf.innerHTML = '';
        var ec = a.emotion_confidence || {};
        for (var ek in ec) {
            var ctag = document.createElement('span');
            ctag.className = 'emo-tag';
            ctag.textContent = ek + ': ' + (ec[ek] * 100).toFixed(0) + '%';
            conf.appendChild(ctag);
        }
    }
    section.scrollIntoView({ behavior: 'smooth' });
}

/* ── Load entries (entries page) ──────────────────────────────────────── */

function loadEntries() {
    var sel = document.getElementById('limit-select');
    var limit = sel ? sel.value : 50;
    var search = '';
    var searchInput = document.getElementById('search-input');
    if (searchInput) search = searchInput.value.trim();
    var emotionSel = document.getElementById('emotion-filter');
    var emotion = emotionSel ? emotionSel.value : '';

    var container = document.getElementById('entries-timeline');
    if (!container) return;
    container.innerHTML = '<p class="loading">Loading entries...</p>';

    var url = '/api/entries?limit=' + limit;
    if (search) url += '&search=' + encodeURIComponent(search);
    if (emotion) url += '&emotion=' + encodeURIComponent(emotion);

    fetch(url)
    .then(function(r) { return r.json(); })
    .then(function(data) {
        var entries = data.entries || [];
        if (entries.length === 0) {
            container.innerHTML = '<p class="loading">No entries found. Start journaling!</p>';
            return;
        }
        container.innerHTML = renderTimeline(entries);
    })
    .catch(function() {
        container.innerHTML = '<p class="loading">Failed to load entries.</p>';
    });
}

function renderTimeline(entries) {
    var html = '';
    entries.forEach(function(e) {
        var color = moodColor(e.mood_score);
        var date = formatDate(e.created_at);
        var excerpt = e.content.length > 200 ? e.content.substring(0, 200) + '...' : e.content;
        html += '<div class="timeline-entry">' +
            '<div class="timeline-dot" style="background:' + color + '"></div>' +
            '<div class="timeline-body">' +
            '<div class="timeline-date">' + date + '</div>' +
            '<div class="timeline-excerpt">' + escapeHtml(excerpt) + '</div>' +
            '<div class="timeline-meta">' +
            '<span class="mood-badge" style="background:' + color + '">' + e.mood_score.toFixed(2) + '</span>' +
            '<span class="emotion-badge">' + e.dominant_emotion + '</span>' +
            '<span class="emo-tag">' + e.word_count + ' words</span>' +
            '</div></div></div>';
    });
    return html;
}

/* ── Load dashboard ───────────────────────────────────────────────────── */

function loadDashboard() {
    // Stats
    fetch('/api/stats')
    .then(function(r) { return r.json(); })
    .then(function(data) {
        var s = data.stats || {};
        var el = document.getElementById('dash-total');
        if (el) el.textContent = s.total_entries || 0;
        el = document.getElementById('dash-avg');
        if (el) el.textContent = (s.avg_mood || 0).toFixed(2);
        el = document.getElementById('dash-emotion');
        if (el) el.textContent = s.top_emotion || '--';

        // Mood distribution
        var dist = s.mood_distribution || {};
        var distEl = document.getElementById('dash-distribution');
        if (distEl) {
            var total = (s.total_entries || 1);
            distEl.innerHTML = buildDistBars(dist, total);
        }
    })
    .catch(function() {});

    // Trends for streak and chart
    fetch('/api/trends?days=7')
    .then(function(r) { return r.json(); })
    .then(function(data) {
        var t = data.trends || {};
        var el = document.getElementById('dash-streak');
        if (el) el.textContent = (t.current_streak || 0) + ' days';

        var scores = (t.day_scores || []).map(function(d) { return d.score; });
        drawLineChart('dash-trend-chart', scores);
    })
    .catch(function() {});

    // Recent entries
    fetch('/api/entries?limit=5')
    .then(function(r) { return r.json(); })
    .then(function(data) {
        var entries = data.entries || [];
        var container = document.getElementById('dash-recent');
        if (!container) return;
        if (entries.length === 0) {
            container.innerHTML = '<p class="loading">No entries yet. <a href="/journal">Write your first entry!</a></p>';
            return;
        }
        container.innerHTML = renderTimeline(entries);
    })
    .catch(function() {});

    // Suggestions
    fetch('/api/suggestions')
    .then(function(r) { return r.json(); })
    .then(function(data) {
        var tips = data.suggestions || [];
        var ul = document.getElementById('dash-suggestions');
        if (!ul) return;
        if (tips.length === 0) {
            ul.innerHTML = '<li>Write a few journal entries to get personalised tips!</li>';
            return;
        }
        ul.innerHTML = tips.map(function(t) { return '<li>' + escapeHtml(t) + '</li>'; }).join('');
    })
    .catch(function() {});
}

/* ── Load analytics ───────────────────────────────────────────────────── */

function loadAnalytics() {
    var sel = document.getElementById('days-select');
    var days = sel ? sel.value : 30;

    fetch('/api/trends?days=' + days)
    .then(function(r) { return r.json(); })
    .then(function(data) {
        var t = data.trends || {};

        var el = document.getElementById('stat-weekly');
        if (el) el.textContent = (t.weekly_avg || 0).toFixed(2);
        el = document.getElementById('stat-monthly');
        if (el) el.textContent = (t.monthly_avg || 0).toFixed(2);
        el = document.getElementById('stat-streak');
        if (el) el.textContent = (t.current_streak || 0) + ' days';

        var ef = t.emotion_frequency || {};
        var topEmo = Object.keys(ef).length ? Object.keys(ef)[0] : '--';
        el = document.getElementById('stat-top-emo');
        if (el) el.textContent = topEmo;

        // Best day
        el = document.getElementById('best-day-info');
        if (el) el.textContent = t.best_day ? formatDate(t.best_day) : '--';

        var scores = (t.day_scores || []).map(function(d) { return d.score; });
        drawLineChart('mood-chart', scores);
        drawBarChart('emotion-chart', ef);

        // Day-of-week chart
        var dow = t.day_of_week_avg || {};
        drawBarChart('dow-chart', dow);
    })
    .catch(function(err) { console.error('trends error', err); });

    // Stats for distribution
    fetch('/api/stats')
    .then(function(r) { return r.json(); })
    .then(function(data) {
        var s = data.stats || {};
        var dist = s.mood_distribution || {};
        var distEl = document.getElementById('mood-distribution');
        if (distEl) {
            distEl.innerHTML = buildDistBars(dist, s.total_entries || 1);
        }
    })
    .catch(function() {});

    // Word cloud
    fetch('/api/word-cloud')
    .then(function(r) { return r.json(); })
    .then(function(data) {
        var words = data.words || {};
        var container = document.getElementById('word-cloud-container');
        if (!container) return;
        var html = '';
        var pos = words.positive || {};
        var neg = words.negative || {};
        var maxCount = 1;
        for (var k in pos) { if (pos[k] > maxCount) maxCount = pos[k]; }
        for (var k2 in neg) { if (neg[k2] > maxCount) maxCount = neg[k2]; }

        for (var pw in pos) {
            var size = 0.7 + (pos[pw] / maxCount) * 1.0;
            html += '<span class="word-tag word-positive" style="font-size:' + size + 'rem">' + pw + ' (' + pos[pw] + ')</span>';
        }
        for (var nw in neg) {
            var nsize = 0.7 + (neg[nw] / maxCount) * 1.0;
            html += '<span class="word-tag word-negative" style="font-size:' + nsize + 'rem">' + nw + ' (' + neg[nw] + ')</span>';
        }
        container.innerHTML = html || '<p class="loading">No word data yet.</p>';
    })
    .catch(function() {});

    // Suggestions
    fetch('/api/suggestions')
    .then(function(r) { return r.json(); })
    .then(function(data) {
        var tips = data.suggestions || [];
        var ul = document.getElementById('analytics-suggestions');
        if (!ul) return;
        ul.innerHTML = tips.map(function(t) { return '<li>' + escapeHtml(t) + '</li>'; }).join('');
    })
    .catch(function() {});
}

/* ── Build distribution bars HTML ─────────────────────────────────────── */

function buildDistBars(dist, total) {
    var categories = [
        { key: 'very_positive', label: 'Very Positive', color: '#16a34a' },
        { key: 'positive', label: 'Positive', color: '#22c55e' },
        { key: 'neutral', label: 'Neutral', color: '#eab308' },
        { key: 'negative', label: 'Negative', color: '#f97316' },
        { key: 'very_negative', label: 'Very Negative', color: '#ef4444' }
    ];
    var html = '';
    categories.forEach(function(c) {
        var count = dist[c.key] || 0;
        var pct = total > 0 ? Math.round((count / total) * 100) : 0;
        html += '<div class="dist-row">' +
            '<span class="dist-label">' + c.label + '</span>' +
            '<div class="dist-bar-bg"><div class="dist-bar" style="width:' + pct + '%;background:' + c.color + '"></div></div>' +
            '<span class="dist-count">' + count + '</span></div>';
    });
    return html;
}

/* ── Canvas line chart ────────────────────────────────────────────────── */

function drawLineChart(canvasId, scores) {
    var canvas = document.getElementById(canvasId);
    if (!canvas) return;
    var ctx = canvas.getContext('2d');
    var W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);

    if (!scores || scores.length === 0) {
        ctx.fillStyle = '#92400e';
        ctx.font = '14px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('No data yet', W / 2, H / 2);
        return;
    }

    var pad = 40;
    var plotW = W - pad * 2, plotH = H - pad * 2;

    /* Grid lines */
    ctx.strokeStyle = '#fde68a';
    ctx.lineWidth = 0.5;
    for (var g = 0; g <= 4; g++) {
        var gy = pad + (plotH / 4) * g;
        ctx.beginPath(); ctx.moveTo(pad, gy); ctx.lineTo(W - pad, gy); ctx.stroke();
    }

    /* Axis labels */
    ctx.fillStyle = '#92400e';
    ctx.font = '11px sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText('1.0', pad - 6, pad + 4);
    ctx.fillText('0.0', pad - 6, pad + plotH / 2 + 4);
    ctx.fillText('-1.0', pad - 6, pad + plotH + 4);

    /* Line */
    ctx.strokeStyle = '#f59e0b';
    ctx.lineWidth = 2.5;
    ctx.lineJoin = 'round';
    ctx.beginPath();
    scores.forEach(function(s, i) {
        var x = pad + (i / Math.max(scores.length - 1, 1)) * plotW;
        var y = pad + ((1 - s) / 2) * plotH;
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.stroke();

    /* Dots */
    scores.forEach(function(s, i) {
        var x = pad + (i / Math.max(scores.length - 1, 1)) * plotW;
        var y = pad + ((1 - s) / 2) * plotH;
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fillStyle = moodColor(s);
        ctx.fill();
    });
}

/* ── Canvas bar chart ─────────────────────────────────────────────────── */

function drawBarChart(canvasId, dataObj) {
    var canvas = document.getElementById(canvasId);
    if (!canvas) return;
    var ctx = canvas.getContext('2d');
    var W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);

    var labels = Object.keys(dataObj);
    var values = Object.values(dataObj);
    if (labels.length === 0) {
        ctx.fillStyle = '#92400e';
        ctx.font = '14px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('No data yet', W / 2, H / 2);
        return;
    }

    var colors = ['#f59e0b', '#22c55e', '#ef4444', '#3b82f6', '#a855f7', '#ec4899', '#14b8a6'];
    var pad = 50, plotW = W - pad * 2, plotH = H - pad - 30;
    var maxV = Math.max.apply(null, values.map(function(v) { return Math.abs(v); })) || 1;
    var gap = plotW / labels.length;
    var barW = gap * 0.6;

    labels.forEach(function(l, i) {
        var val = Math.abs(values[i]);
        var barH = (val / maxV) * plotH;
        var x = pad + gap * i + (gap - barW) / 2;
        var y = pad + plotH - barH;
        ctx.fillStyle = colors[i % colors.length];

        // roundRect fallback
        if (ctx.roundRect) {
            ctx.beginPath();
            ctx.roundRect(x, y, barW, barH, [4, 4, 0, 0]);
            ctx.fill();
        } else {
            ctx.fillRect(x, y, barW, barH);
        }

        ctx.fillStyle = '#422006';
        ctx.font = '11px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(l, x + barW / 2, H - 6);

        var displayVal = typeof values[i] === 'number' ? values[i].toFixed ? values[i].toFixed(2) : values[i] : values[i];
        ctx.fillText(displayVal, x + barW / 2, y - 6);
    });
}

/* ── Insights page (if it exists) ─────────────────────────────────────── */

function loadInsights() {
    loadAnalytics();
}
