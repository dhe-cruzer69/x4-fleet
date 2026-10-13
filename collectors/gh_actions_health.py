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
        response = client.get(
            f"{API}/repos/{owner}/{repo}/actions/runs",
            headers=headers(token),
            params={"per_page": limit},
        )
        # Do not silently convert permission or visibility errors into "no runs".
        response.raise_for_status()
        return response.json().get("workflow_runs", [])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", default="data/inventory.json")
    parser.add_argument("--token", default=os.environ.get("GH_FLEET_TOKEN"))
    parser.add_argument("--owner", default=os.environ.get("GITHUB_OWNER", "dhe-cruzer69"))
    args = parser.parse_args()

    if not args.token:
        print("GH_FLEET_TOKEN required", file=sys.stderr)
        raise SystemExit(1)

    inventory = json.loads(Path(args.inventory).read_text(encoding="utf-8"))
    failures = []
    checked = 0
    for repo in inventory.get("repos", []):
        if repo.get("archived"):
            continue
        name = repo["name"]
        runs = recent_runs(args.owner, name, args.token)
        checked += 1
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
                break

    report = {
        "generated_at": inventory.get("generated_at"),
        "repositories_checked": checked,
        "failing_repos": len(failures),
        "failures": failures,
    }
    out = Path("data/metrics/actions_health.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Repositories checked: {checked}; failing workflows: {len(failures)}")
    for failure in failures:
        print(f"  {failure['repo']}: {failure['workflow']} ({failure['html_url']})")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
