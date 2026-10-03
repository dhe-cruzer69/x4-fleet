"""Unit tests for x4-fleet collectors."""
from __future__ import annotations

from datetime import datetime, timezone

from collectors.gh_inventory import compute_staleness, summarize


def test_summarize_minimal():
    raw = {
        "name": "x4-beast",
        "full_name": "dhe-cruzer69/x4-beast",
        "private": False,
        "fork": False,
        "archived": False,
        "description": "Flagship",
        "language": "Python",
        "stargazers_count": 0,
        "open_issues_count": 0,
        "size": 31,
        "default_branch": "main",
        "pushed_at": "2026-09-23T23:49:01Z",
        "html_url": "https://github.com/dhe-cruzer69/x4-beast",
        "topics": ["ai-agents", "mcp"],
        "has_issues": True,
        "visibility": "public",
    }
    s = summarize(raw)
    assert s["name"] == "x4-beast"
    assert s["stars"] == 0
    assert s["topics"] == ["ai-agents", "mcp"]


def test_compute_staleness_recent():
    now = datetime(2026, 10, 3, tzinfo=timezone.utc)
    days = compute_staleness("2026-09-23T23:49:01Z", now)
    assert 9 <= days <= 11


def test_compute_staleness_missing():
    now = datetime.now(timezone.utc)
    assert compute_staleness(None, now) == 999
