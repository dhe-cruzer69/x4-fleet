"""Authenticated GitHub repository inventory with private-coverage guardrails."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
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
    """List repositories visible to the authenticated user, scoped to owner."""
    repos: list[dict[str, Any]] = []
    page = 1
    with httpx.Client(timeout=60.0) as client:
        while True:
            response = client.get(
                f"{API}/user/repos",
                headers=github_headers(token),
                params={
                    "per_page": 100,
                    "page": page,
                    "affiliation": "owner,collaborator,organization_member",
                    "sort": "updated",
                    "direction": "desc",
                },
            )
            response.raise_for_status()
            batch = response.json()
            if not batch:
                break
            repos.extend(
                repo for repo in batch
                if repo.get("owner", {}).get("login", "").casefold() == owner.casefold()
            )
            if len(batch) < 100:
                break
            page += 1

    unique: dict[int, dict[str, Any]] = {}
    for repo in repos:
        unique[repo["id"]] = repo
    return list(unique.values())


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
        dt = datetime.fromisoformat(pushed_at)
        return max(0, (now - dt).days)
    except ValueError:
        return 999


def main() -> None:
    parser = argparse.ArgumentParser(description="X4 Fleet GitHub inventory collector")
    parser.add_argument("--owner", default=os.environ.get("GITHUB_OWNER", "dhe-cruzer69"))
    parser.add_argument("--out", default="data/inventory.json")
    parser.add_argument("--token", default=os.environ.get("GH_FLEET_TOKEN"))
    parser.add_argument(
        "--min-private", type=int, default=1,
        help="Fail closed when fewer than this many private repositories are visible.",
    )
    args = parser.parse_args()

    if not args.token:
        print("GH_FLEET_TOKEN required; refusing to publish incomplete inventory.", file=sys.stderr)
        raise SystemExit(1)
    if args.min_private < 0:
        parser.error("--min-private must be >= 0")

    now = datetime.now(UTC)
    raw = list_repos(args.owner, args.token)
    items = []
    for repo in raw:
        item = summarize(repo)
        item["staleness_days"] = compute_staleness(item["pushed_at"], now)
        item["health"] = "stale" if item["staleness_days"] > 14 else "ok"
        if item["size_kb"] == 0 and not item["fork"]:
            item["health"] = "empty_stub"
        items.append(item)

    inventory = {
        "schema_version": "1.0.0",
        "generated_at": now.isoformat(),
        "owner": args.owner,
        "total": len(items),
        "public": sum(1 for item in items if not item["private"]),
        "private": sum(1 for item in items if item["private"]),
        "archived": sum(1 for item in items if item["archived"]),
        "empty_stubs": sum(1 for item in items if item["health"] == "empty_stub"),
        "stale": sum(1 for item in items if item["health"] == "stale"),
        "repos": sorted(items, key=lambda item: item["name"].casefold()),
    }

    if inventory["private"] < args.min_private:
        print(
            f"INCOMPLETE INVENTORY: private={inventory['private']} < "
            f"required={args.min_private}; check X4_FLEET_TOKEN permissions.",
            file=sys.stderr,
        )
        raise SystemExit(2)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    print(
        f"Wrote {inventory['total']} repositories to {out}; "
        f"public={inventory['public']} private={inventory['private']}"
    )


if __name__ == "__main__":
    main()
