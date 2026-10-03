#!/usr/bin/env python3
"""Detect failing GitHub Actions workflows and emit structured findings."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import httpx

API = "https://api.github.com"


def headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def recent_runs(owner: str, repo: str, token: str, limit: int = 5) -> list[dict[str, Any]]:
    with httpx.Client(timeout=30.0) as client:
        r = client.get(
            f"{API}/repos/{owner}/{repo}/actions/runs",
            headers=headers(token),
            params={"per_page": limit},
        )
        if r.status_code == 404:
            return []
        r.raise_for_status()
        return r.json().get("workflow_runs", [])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", default="data/inventory.json")
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"))
    parser.add_argument("--owner", default=os.environ.get("GITHUB_OWNER", "dhe-cruzer69"))
    args = parser.parse_args()

    if not args.token:
        print("GITHUB_TOKEN required", file=sys.stderr)
        sys.exit(1)

    inv = json.loads(Path(args.inventory).read_text())
    failures = []
    for repo in inv.get("repos", []):
        if repo.get("archived") or repo.get("private"):
            continue
        name = repo["name"]
        runs = recent_runs(args.owner, name, args.token)
        for run in runs:
            if run.get("conclusion") == "failure":
                failures.append({
                    "repo": name,
                    "workflow": run.get("name"),
                    "run_id": run.get("id"),
                    "html_url": run.get("html_url"),
                    "head_sha": run.get("head_sha", "")[:7],
                    "created_at": run.get("created_at"),
                })
                break  # one failure per repo is enough for the report

    report = {
        "generated_at": inv.get("generated_at"),
        "failing_repos": len(failures),
        "failures": failures,
    }
    out = Path("data/metrics/actions_health.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Failing workflows: {len(failures)}")
    for f in failures:
        print(f"  {f['repo']}: {f['workflow']} ({f['html_url']})")


if __name__ == "__main__":
    main()
