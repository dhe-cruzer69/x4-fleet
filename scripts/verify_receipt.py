"""Validate deployment receipts, including cross-field invariants."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any

DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
REQUIRED = {
    "schema_version",
    "deployment_id",
    "release_run_id",
    "target",
    "status",
    "requested_digest",
    "observed_digest",
    "source_commit",
    "started_at_utc",
    "finished_at_utc",
    "readiness",
    "rollback",
}


def valid_utc(value: Any) -> bool:
    """Return true only for valid RFC3339-shaped UTC timestamps ending in Z."""
    if not isinstance(value, str) or not UTC_RE.fullmatch(value):
        return False
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return False
    return True


def validate_receipt(data: Any) -> list[str]:
    """Return receipt contract errors; successful receipts require matching digests."""
    if not isinstance(data, dict):
        return ["receipt root must be an object"]

    errors: list[str] = []
    missing = REQUIRED - data.keys()
    extra = data.keys() - (REQUIRED | {"error"})
    if missing:
        errors.append("missing required fields: " + ", ".join(sorted(missing)))
    if extra:
        errors.append("unknown fields: " + ", ".join(sorted(extra)))
    if errors:
        return errors

    if data["schema_version"] != "1":
        errors.append("unsupported schema_version")

    for field in ("deployment_id", "target"):
        if not isinstance(data[field], str) or not data[field].strip():
            errors.append(f"{field} must be a non-empty string")

    if type(data["release_run_id"]) is not int or data["release_run_id"] < 1:
        errors.append("release_run_id must be a positive integer")

    if data["status"] not in {"blocked", "deploying", "succeeded", "failed"}:
        errors.append("invalid status")

    for field in ("requested_digest", "observed_digest"):
        value = data[field]
        if value is not None and (not isinstance(value, str) or not DIGEST_RE.fullmatch(value)):
            errors.append(f"invalid {field}")

    source_commit = data["source_commit"]
    if source_commit is not None and (
        not isinstance(source_commit, str)
        or not re.fullmatch(r"(?:[a-f0-9]{40}|[a-f0-9]{64})", source_commit)
    ):
        errors.append("invalid source_commit")

    if not valid_utc(data["started_at_utc"]):
        errors.append("started_at_utc must be valid RFC3339 UTC")

    finished = data["finished_at_utc"]
    if finished is not None and not valid_utc(finished):
        errors.append("finished_at_utc must be valid RFC3339 UTC or null")

    if data["readiness"] is not None and not isinstance(data["readiness"], dict):
        errors.append("readiness must be an object or null")

    rollback = data["rollback"]
    if not isinstance(rollback, dict):
        errors.append("rollback must be an object")
    else:
        if set(rollback) - {"attempted", "status", "observed_digest"}:
            errors.append("rollback has unknown fields")
        attempted = rollback.get("attempted")
        state = rollback.get("status")
        if type(attempted) is not bool:
            errors.append("rollback.attempted must be boolean")
        if state not in {"not_attempted", "attempted", "verified", "failed"}:
            errors.append("invalid rollback.status")
        if state == "not_attempted" and attempted is not False:
            errors.append("not_attempted rollback must have attempted=false")
        if state in {"attempted", "verified", "failed"} and attempted is not True:
            errors.append("attempted rollback states require attempted=true")
        rollback_digest = rollback.get("observed_digest")
        if rollback_digest is not None and (
            not isinstance(rollback_digest, str) or not DIGEST_RE.fullmatch(rollback_digest)
        ):
            errors.append("invalid rollback.observed_digest")
        if state == "verified" and not isinstance(rollback_digest, str):
            errors.append("verified rollback requires observed_digest")

    if data["status"] == "succeeded":
        requested = data["requested_digest"]
        observed = data["observed_digest"]
        if not isinstance(requested, str) or not DIGEST_RE.fullmatch(requested):
            errors.append("succeeded receipt requires valid requested_digest")
        if not isinstance(observed, str) or not DIGEST_RE.fullmatch(observed):
            errors.append("succeeded receipt requires valid observed_digest")
        if isinstance(requested, str) and isinstance(observed, str) and requested != observed:
            errors.append("requested_digest must equal observed_digest for succeeded receipts")
        if not valid_utc(finished):
            errors.append("succeeded receipt requires valid finished_at_utc")
        if not isinstance(data["readiness"], dict):
            errors.append("succeeded receipt requires readiness evidence")

    return errors
