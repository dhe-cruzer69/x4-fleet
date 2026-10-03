# x4-fleet

**Self-healing AI agent fleet with evidence ledger, nightly audit, and automatic issue generation.**

> Part of the X4 / ARIEX4Ops / ARIEXCORE ecosystem — local-first, evidence-first, policy-gated autonomy.

[![CI](https://github.com/dhe-cruzer69/x4-fleet/actions/workflows/ci.yml/badge.svg)](https://github.com/dhe-cruzer69/x4-fleet/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://python.org)

One repo that replaces 30+ stub repos. Collects inventory + metrics for every repository under your account, detects staleness / CI failures / missing metadata, opens issues, and (for Level 2 repos) can propose trivial autofix PRs.

## Trending topics this repo targets (Oct 2026)

`ai-agents` · `mcp` · `self-healing` · `fleet-management` · `observability` · `github-actions` · `agent-framework` · `local-first`

## Architecture

```
x4-fleet/
├── data/
│   ├── inventory.json          # every repo: name, purpose, status, freshness, health
│   ├── inventory.sample.json   # example snapshot
│   ├── metrics/                # daily snapshots
│   └── evidence/               # OBSERVED → VALIDATED ledger + schema.json
├── collectors/
│   ├── gh_inventory.py         # GitHub API full repo list + staleness
│   └── gh_actions_health.py    # workflow failure detection
├── healing/
│   ├── policies.yml            # autonomy levels (0–3)
│   └── autoheal.yml            # declarative triggers
├── publish/
│   ├── topics.yml              # recommended GitHub topics
│   └── README.generator.md     # profile table generator notes
├── tests/
│   └── test_inventory.py
└── .github/workflows/
    ├── ci.yml                  # lint + typecheck + pytest (3.11/3.12)
    ├── nightly-audit.yml       # cron 02:00 IST
    └── weekly-report.yml       # Monday fleet report issue
```

## Quick Start

```bash
pip install -e ".[dev]"
export GITHUB_TOKEN=ghp_...   # fine-grained: Contents + Issues + Metadata
python -m collectors.gh_inventory --owner dhe-cruzer69 --out data/inventory.json
python -m collectors.gh_actions_health --inventory data/inventory.json
pytest -q
```

## Autonomy Levels

| Level | Name | Allowed |
|-------|------|---------|
| 0 | Observe | Read → inspect → report |
| 1 | Assist | Read → plan → patch → open PR |
| 2 | Governed Autopilot | Plan → policy → execute → verify → recover |
| 3 | Never | Delete, secrets, force-push, financial |

## Quality Gate

Nothing is "done" until inventory runs green nightly, zero repos stale >14d, zero failing workflows on flagship repos, twin pairs merged, empty stubs archived. Until then: **UNKNOWN**.

## Related

- [x4-beast](https://github.com/dhe-cruzer69/x4-beast) · [x4-autofix](https://github.com/dhe-cruzer69/x4-autofix) · [x4-evidence](https://github.com/dhe-cruzer69/x4-evidence) · [ariexcore-beast-mode](https://github.com/dhe-cruzer69/ariexcore-beast-mode)

## License

Apache-2.0
