from __future__ import annotations

from pathlib import Path

import pytest

from collectors.ci_suppression_audit import scan_roots


def test_flags_lint_suppression_and_ignores_cleanup(tmp_path: Path) -> None:
    repo = tmp_path / "sample-repo"
    workflow = repo / ".github" / "workflows" / "ci.yml"
    script = repo / "scripts" / "cleanup.sh"
    workflow.parent.mkdir(parents=True)
    script.parent.mkdir(parents=True)
    workflow.write_text("run: ruff check . || true\n", encoding="utf-8")
    script.write_text("docker rm -f test-container || true\n", encoding="utf-8")

    findings = scan_roots([repo])

    assert len(findings) == 2
    quality = next(item for item in findings if item.rule == "SHELL_FAILURE_SUPPRESSION" and item.path.endswith("ci.yml"))
    cleanup = next(item for item in findings if item.path.endswith("cleanup.sh"))
    assert quality.severity == "high"
    assert cleanup.severity == "info"


def test_rejects_missing_repository_path(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="not a directory"):
        scan_roots([tmp_path / "missing"])


def test_ignores_literal_suppression_pattern_in_grep_rule(tmp_path: Path) -> None:
    repo = tmp_path / "sample-repo"
    script = repo / "scripts" / "verify-repo.sh"
    script.parent.mkdir(parents=True)
    script.write_text("grep -RInF '|| true' .\n", encoding="utf-8")

    assert scan_roots([repo]) == []
