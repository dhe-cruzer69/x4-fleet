"""Adversarial tests for the X4 BEASTMODE local contracts."""
from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.fleet_scorecard import build_scorecard
from scripts.verify_receipt import validate_receipt
from scripts.verify_release import validate_manifest

DIGEST = "sha256:" + "d" * 64
RECEIPT = {
    "schema_version": "1", "deployment_id": "dep-1", "release_run_id": 123,
    "target": "staging", "status": "succeeded", "requested_digest": DIGEST,
    "observed_digest": DIGEST, "source_commit": "a" * 40,
    "started_at_utc": "2026-10-19T12:00:00Z",
    "finished_at_utc": "2026-10-19T12:01:00Z",
    "readiness": {"http": 200, "healthy": True},
    "rollback": {"attempted": False, "status": "not_attempted"},
}

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
    "created_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
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
    assert any("RFC3339 UTC timestamp" in error
               for error in validate_manifest(dict(VALID, created_at_utc="2026-99-99T29:99:99Z")))


def test_manifest_rejects_non_rfc3339_timestamp_shapes():
    for timestamp in ("not-a-dateZ", "2026-10-19 12:00:00Z", "2026-10-19T12:00Z", "2026-10-19T12:00:00+00:00"):
        assert validate_manifest(dict(VALID, created_at_utc=timestamp))


def test_manifest_rejects_mutable_tag_and_wrong_registry():
    for image in ("docker.io/team/image", "ghcr.io/dhe-cruzer69/x4-fleet:latest"):
        assert any("invalid image repository" in error
                   for error in validate_manifest(dict(VALID, image=image)))


def test_schema_documents_are_valid_and_validate_release_instance():
    for path in sorted((ROOT / "schemas").glob("*.schema.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        if path.name == "release-manifest.schema.json":
            assert list(validator.iter_errors(VALID)) == []
        if path.name == "deployment-receipt.schema.json":
            assert list(validator.iter_errors(RECEIPT)) == []


def test_receipt_rejects_success_with_digest_mismatch():
    bad = dict(RECEIPT, observed_digest="sha256:" + "e" * 64)
    assert any("must equal" in error for error in validate_receipt(bad))


def test_receipt_rejects_unverified_rollback():
    bad = dict(RECEIPT, rollback={"attempted": False, "status": "verified"})
    assert any("attempted=true" in error or "requires attempted=true" in error for error in validate_receipt(bad))


def test_scorecard_does_not_invent_a_score():
    result = build_scorecard({
        "generated_at": "2026-10-19T00:00:00Z",
        "total": 1,
        "repos": [{"full_name": "owner/repo", "archived": False, "private": True, "pushed_at": None}],
    })
    assert result["status"] == "OBSERVED"
    assert result["score"] is None
    assert result["missing_push_timestamp"] == 1
    assert result["private_repositories_observed"] == 1


def test_scorecard_fails_closed_on_duplicate_names():
    result = build_scorecard({
        "generated_at": "2026-10-19T00:00:00Z",
        "total": 2,
        "repos": [{"full_name": "owner/same", "archived": False}, {"full_name": "owner/same", "archived": False}],
    })
    assert result["status"] == "UNKNOWN"
    assert result["duplicate_names"] == ["owner/same"]


def test_scorecard_fails_closed_on_truncated_inventory():
    result = build_scorecard({
        "generated_at": "2026-10-19T00:00:00Z",
        "total": 2,
        "repos": [{"full_name": "owner/repo", "archived": False}],
    })
    assert result["status"] == "UNKNOWN"
    assert any("inventory is incomplete" in error for error in result["validation_errors"])


def test_scorecard_rejects_bad_timestamp_and_missing_full_name():
    result = build_scorecard({
        "generated_at": "not-a-date",
        "total": 1,
        "repos": [{"name": "repo", "archived": False, "pushed_at": 12345}],
    })
    assert result["status"] == "UNKNOWN"
    assert any("generated_at" in error for error in result["validation_errors"])
    assert any("full_name" in error for error in result["validation_errors"])


def test_scorecard_rejects_bad_root_and_repos_shape():
    for value in ([], {}, {"repos": {}}):
        try:
            build_scorecard(value)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid inventory must be rejected")
