#!/usr/bin/env python3
"""GitHub full inventory collector for x4-fleet.

Pulls every repository for an owner, extracts metadata, CI status hints,
and writes a versioned inventory.json suitable for nightly diffs.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

API = "https://api.github.com"


def github_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def list_repos(owner: str, token: str) -> list[dict[str, Any]]:
    repos: list[dict[str, Any]] = []
    page = 1
    with httpx.Client(timeout=60.0) as client:
        while True:
            r = client.get(
                f"{API}/users/{owner}/repos",
                headers=github_headers(token),
                params={"per_page": 100, "page": page, "type": "all", "sort": "updated"},
            )
            r.raise_for_status()
            batch = r.json()
            if not batch:
                break
            repos.extend(batch)
            page += 1
            if page > 20:  # safety
                break
    return repos


def summarize(repo: dict[str, Any]) -> dict[str, Any]:
    pushed = repo.get("pushed_at") or repo.get("updated_at")
    return {
        "name": repo["name"],
        "full_name": repo["full_name"],
        "private": repo.get("private", False),
        "fork": repo.get("fork", False),
        "archived": repo.get("archived", False),
        "description": repo.get("description") or "",
        "language": repo.get("language"),
        "stars": repo.get("stargazers_count", 0),
        "open_issues": repo.get("open_issues_count", 0),
        "size_kb": repo.get("size", 0),
        "default_branch": repo.get("default_branch", "main"),
        "pushed_at": pushed,
        "html_url": repo.get("html_url"),
        "topics": repo.get("topics") or [],
        "has_issues": repo.get("has_issues", True),
        "visibility": repo.get("visibility", "public" if not repo.get("private") else "private"),
    }


def compute_staleness(pushed_at: str | None, now: datetime) -> int:
    if not pushed_at:
        return 999
    try:
        dt = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
        return (now - dt).days
    except Exception:
        return 999


def main() -> None:
    parser = argparse.ArgumentParser(description="X4 Fleet GitHub inventory collector")
    parser.add_argument("--owner", default=os.environ.get("GITHUB_OWNER", "dhe-cruzer69"))
    parser.add_argument("--out", default="data/inventory.json")
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"))
    args = parser.parse_args()

    if not args.token:
        print("GITHUB_TOKEN required", file=sys.stderr)
        sys.exit(1)

    now = datetime.now(timezone.utc)
    raw = list_repos(args.owner, args.token)
    items = []
    for r in raw:
        s = summarize(r)
        s["staleness_days"] = compute_staleness(s["pushed_at"], now)
        s["health"] = "stale" if s["staleness_days"] > 14 else "ok"
        if s["size_kb"] == 0 and not s["fork"]:
            s["health"] = "empty_stub"
        items.append(s)

    inventory = {
        "generated_at": now.isoformat(),
        "owner": args.owner,
        "total": len(items),
        "public": sum(1 for i in items if not i["private"]),
        "private": sum(1 for i in items if i["private"]),
        "archived": sum(1 for i in items if i["archived"]),
        "empty_stubs": sum(1 for i in items if i["health"] == "empty_stub"),
        "stale": sum(1 for i in items if i["health"] == "stale"),
        "repos": sorted(items, key=lambda x: x["name"]),
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(items)} repos → {out}")
    print(f"  empty_stubs={inventory['empty_stubs']}  stale={inventory['stale']}")


if __name__ == "__main__":
    main()
