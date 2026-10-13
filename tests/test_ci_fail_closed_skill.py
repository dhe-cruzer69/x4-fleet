from pathlib import Path


def test_ci_fail_closed_skill_has_required_contract_sections() -> None:
    content = Path("skills/ci-fail-closed/SKILL.md").read_text(encoding="utf-8")
    assert content.startswith("---\nname: ci-fail-closed\n")
    assert "description: Use when" in content
    assert "## Core contract" in content
    assert "## Required procedure" in content
    assert "## Red flags" in content
    assert "## Evidence and reporting" in content
    assert "does not authorize merging" in content
