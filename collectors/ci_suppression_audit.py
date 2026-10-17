"""Audit local repository trees for CI false-green suppression patterns.

This tool is read-only. It reports suspicious quality-gate suppression; it never
rewrites files, creates branches, or merges pull requests.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "dist", "build", "__pycache__"}
SHELL_SUFFIXES = {".sh", ".bash", ".ps1"}
WORKFLOW_SUFFIXES = {".yml", ".yaml"}
SUPPRESSION = re.compile(r"(?<!['\"\w])\|\|\s*(?:true\b|echo\b)")
CONTINUE_ON_ERROR = re.compile(r"^\s*continue-on-error\s*:\s*true\b", re.IGNORECASE)
QUALITY_WORDS = re.compile(
    r"lint|ruff|mypy|pytest|test|type.?check|build|deploy|health|verify|quality|pip install|git push",
    re.IGNORECASE,
)
CLEANUP_WORDS = re.compile(r"docker (?:rm|stop|kill)\b|preview\.mjs stop|pkill\b", re.IGNORECASE)


@dataclass(frozen=True)
class Finding:
    repository: str
    path: str
    line: int
    rule: str
    severity: str
    message: str
    excerpt: str


def _eligible(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    if any(part in SKIP_DIRS for part in relative.parts):
        return False
    if path.suffix.lower() in SHELL_SUFFIXES:
        return True
    return (
        path.suffix.lower() in WORKFLOW_SUFFIXES
        and ".github" in relative.parts
        and "workflows" in relative.parts
    )


def scan_roots(roots: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for supplied_root in roots:
        root = supplied_root.resolve()
        if not root.is_dir():
            raise ValueError(f"Repository path is not a directory: {supplied_root}")
        repo_name = root.name
        for path in sorted(root.rglob("*")):
            if not path.is_file() or not _eligible(path, root):
                continue
            try:
                lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError as exc:
                findings.append(Finding(
                    repository=repo_name,
                    path=str(path.relative_to(root)),
                    line=1,
                    rule="READ_ERROR",
                    severity="high",
                    message=f"Could not read candidate CI file: {exc}",
                    excerpt="",
                ))
                continue

            for line_number, line in enumerate(lines, start=1):
                relative_path = str(path.relative_to(root))
                if CONTINUE_ON_ERROR.search(line):
                    intentional_upload = "sarif" in line.lower() or "upload" in line.lower()
                    quality_context = bool(QUALITY_WORDS.search(line))
                    severity = "info" if intentional_upload and not quality_context else "high"
                    findings.append(Finding(
                        repo_name, relative_path, line_number, "CONTINUE_ON_ERROR",
                        severity,
                        "Step errors are non-blocking; confirm this is not a required quality gate.",
                        line.strip(),
                    ))
                    continue

                match = SUPPRESSION.search(line)
                if not match:
                    continue
                command = line[:match.start()].strip()
                if CLEANUP_WORDS.search(command):
                    severity = "info"
                    message = "Best-effort cleanup suppression; verify it cannot hide a quality-gate failure."
                elif command.startswith("git commit") and "no changes" in line.lower():
                    severity = "info"
                    message = "Idempotent no-change commit handling; keep separate from test/build gates."
                else:
                    severity = "high" if QUALITY_WORDS.search(command) or ".github/workflows" in relative_path else "medium"
                    message = "A command failure may be suppressed; required checks must fail closed."
                findings.append(Finding(
                    repo_name, relative_path, line_number, "SHELL_FAILURE_SUPPRESSION",
                    severity, message, line.strip(),
                ))
    return findings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repositories", nargs="+", type=Path, help="Local repository root paths")
    parser.add_argument("--json-out", type=Path, help="Optional JSON report destination")
    args = parser.parse_args()

    try:
        findings = scan_roots(args.repositories)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from exc

    payload = {
        "schema_version": "1.0.0",
        "repositories_scanned": len(args.repositories),
        "finding_count": len(findings),
        "high_severity_count": sum(item.severity == "high" for item in findings),
        "findings": [asdict(item) for item in findings],
    }
    rendered = json.dumps(payload, indent=2)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    if payload["high_severity_count"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
