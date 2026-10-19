"""Calculate a read-only fleet scorecard from an existing inventory JSON file."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def build_scorecard(data: Any) -> dict[str, Any]:
    """Return counts and explicit unknowns; intentionally does not invent a percentage."""
    if not isinstance(data, dict):
        raise ValueError("inventory root must be an object")
    repos = data.get("repos")
    if not isinstance(repos, list):
        raise ValueError("inventory field 'repos' must be an array")

    names: set[str] = set()
    duplicates: list[str] = []
    invalid: list[str] = []
    archived = private = stale_unknown = 0
    for index, repo in enumerate(repos):
        if not isinstance(repo, dict):
            invalid.append(f"repos[{index}] is not an object")
            continue
        name = repo.get("full_name") or repo.get("name")
        if not isinstance(name, str) or not name.strip():
            invalid.append(f"repos[{index}] has no valid name")
            continue
        if name in names:
            duplicates.append(name)
        names.add(name)
        if type(repo.get("archived", False)) is not bool:
            invalid.append(f"{name}: archived must be boolean")
        elif repo.get("archived", False):
            archived += 1
        if "private" in repo:
            if type(repo["private"]) is not bool:
                invalid.append(f"{name}: private must be boolean")
            elif repo["private"]:
                private += 1
        if not repo.get("pushed_at"):
            stale_unknown += 1

    complete = not invalid and not duplicates and bool(data.get("generated_at"))
    return {
        "schema_version": "1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "source_generated_at": data.get("generated_at"),
        "status": "OBSERVED" if complete else "UNKNOWN",
        "total_records": len(repos),
        "unique_named_repositories": len(names),
        "archived_repositories": archived,
        "private_repositories_observed": private,
        "missing_push_timestamp": stale_unknown,
        "duplicate_names": sorted(set(duplicates)),
        "validation_errors": invalid,
        "score": None,
        "score_reason": "No percentage score: required policy thresholds and complete source provenance are not established by this input alone.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", default="data/inventory.json")
    parser.add_argument("--out", default="-", help="Output JSON path, or '-' for stdout")
    args = parser.parse_args(argv)
    try:
        data = json.loads(Path(args.inventory).read_text(encoding="utf-8"))
        report = build_scorecard(data)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: scorecard unavailable ({type(exc).__name__}: {exc})", file=sys.stderr)
        return 1
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out == "-":
        print(rendered, end="")
    else:
        output = Path(args.out)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    return 0 if report["status"] == "OBSERVED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
