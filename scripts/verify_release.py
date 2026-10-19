"""Validate the X4 BEASTMODE release manifest without network access."""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
IMAGE_RE = re.compile(
    r"^ghcr\\.io/[a-z0-9]+(?:[._-][a-z0-9]+)*/"
    r"[a-z0-9]+(?:[._-][a-z0-9]+)*(?:/[a-z0-9]+(?:[._-][a-z0-9]+)*)*$"
)
REQUIRED = {
    "schema_version", "repository", "commit_sha", "workflow_run_id",
    "workflow_attempt", "image", "image_digest", "sbom_digest",
    "quality_status", "security_status", "integration_status", "created_at_utc",
}


def validate_manifest(data: Any) -> list[str]:
    """Return validation errors; never treat malformed input as a valid manifest."""
    if not isinstance(data, dict):
        return ["manifest root must be an object"]

    errors: list[str] = []
    missing, extra = REQUIRED - data.keys(), data.keys() - REQUIRED
    if missing:
        errors.append("missing fields: " + ", ".join(sorted(missing)))
    if extra:
        errors.append("unknown fields: " + ", ".join(sorted(extra)))
    if errors:
        return errors

    string_fields = (
        "schema_version", "repository", "commit_sha", "image", "image_digest",
        "sbom_digest", "quality_status", "security_status", "integration_status",
        "created_at_utc",
    )
    for field in string_fields:
        if type(data[field]) is not str:
            errors.append(f"{field} must be a string")
    for field in ("workflow_run_id", "workflow_attempt"):
        # bool is a subclass of int; require exact type.
        if type(data[field]) is not int or data[field] < 1:
            errors.append(f"{field} must be a positive integer")
    if errors:
        return errors

    if data["schema_version"] != "1":
        errors.append("unsupported schema_version")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", data["repository"]):
        errors.append("invalid repository identity")
    if not COMMIT_RE.fullmatch(data["commit_sha"]):
        errors.append("invalid commit_sha")
    if not IMAGE_RE.fullmatch(data["image"]):
        errors.append("invalid image repository")
    for field in ("image_digest", "sbom_digest"):
        if not DIGEST_RE.fullmatch(data[field]):
            errors.append(f"invalid {field}")
    for field in ("quality_status", "security_status", "integration_status"):
        if data[field] != "PASS":
            errors.append(f"{field} must be PASS")
    timestamp = data["created_at_utc"]
    if not timestamp.endswith("Z"):
        errors.append("created_at_utc must be UTC with Z suffix")
    else:
        try:
            parsed = datetime.fromisoformat(timestamp[:-1] + "+00:00")
            if parsed.utcoffset() is None:
                errors.append("created_at_utc must be timezone-aware")
        except ValueError:
            errors.append("invalid created_at_utc")
    return errors


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("Usage: python scripts/verify_release.py <manifest.json>", file=sys.stderr)
        return 2
    path = Path(args[0])
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read manifest ({type(exc).__name__})", file=sys.stderr)
        return 1
    errors = validate_manifest(data)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Manifest schema checks passed: {data['image']}@{data['image_digest']}")
    print("NOTE: schema validation does not prove gates or provenance; verify those independently.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
