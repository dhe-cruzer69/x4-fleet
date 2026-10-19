"""Adversarial tests for the X4 BEASTMODE local contracts."""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.fleet_scorecard import build_scorecard  # noqa: E402
from scripts.verify_release import validate_manifest  # noqa: E402

VALID = {
    "schema_version": "1",
    "repository": "dhe-cruzer69/x4-fleet",
    "commit_sha": "a" * 40,
    "workflow_run_id": 123,
    "workflow_attempt": 1,
    "image": "ghcr.io/dhe-cruzer69/x4-fleet",
    "image_digest": "sha256:" + "b" * 64,
    "sbom_digest": "sha256:" + "c" * 64,
    "quality_status": "PASS",
    "security_status": "PASS",
    "integration_status": "PASS",
    "created_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
}


def test_valid_release_manifest_passes_schema_checks():
    assert validate_manifest(VALID) == []


def test_manifest_rejects_unknown_and_missing_fields():
    bad = dict(VALID)
    bad.pop("repository")
    bad["surprise"] = "value"
    errors = validate_manifest(bad)
    assert any("missing fields" in error for error in errors)
    assert any("unknown fields" in error for error in errors)


def test_manifest_rejects_boolean_as_run_id():
    assert any("workflow_run_id must be a positive integer" in error
               for error in validate_manifest(dict(VALID, workflow_run_id=True)))


def test_manifest_rejects_non_pass_gate():
    assert any("security_status must be PASS" in error
               for error in validate_manifest(dict(VALID, security_status="SKIPPED")))


def test_manifest_rejects_invalid_digest():
    assert any("invalid image_digest" in error
               for error in validate_manifest(dict(VALID, image_digest="sha256:abc")))


def test_manifest_rejects_calendar_invalid_timestamp():
    assert any("invalid created_at_utc" in error
               for error in validate_manifest(dict(VALID, created_at_utc="2026-99-99T29:99:99Z")))


def test_manifest_rejects_mutable_or_wrong_registry_image():
    assert any("invalid image repository" in error
               for error in validate_manifest(dict(VALID, image="docker.io/team/image")))


def test_scorecard_does_not_invent_a_score():
    result = build_scorecard({
        "generated_at": "2026-10-19T00:00:00Z",
        "repos": [{"name": "owner/repo", "archived": False, "private": True, "pushed_at": None}],
    })
    assert result["status"] == "OBSERVED"
    assert result["score"] is None
    assert result["missing_push_timestamp"] == 1
    assert result["private_repositories_observed"] == 1


def test_scorecard_fails_closed_on_duplicate_names():
    result = build_scorecard({
        "generated_at": "2026-10-19T00:00:00Z",
        "repos": [{"name": "same"}, {"name": "same"}],
    })
    assert result["status"] == "UNKNOWN"
    assert result["duplicate_names"] == ["same"]


def test_scorecard_rejects_bad_root_and_repos_shape():
    for value in ([], {}, {"repos": {}}):
        try:
            build_scorecard(value)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid inventory must be rejected")
