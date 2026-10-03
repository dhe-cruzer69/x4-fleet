# x4-fleet

**Self-healing AI agent fleet with evidence ledger, nightly audit, and automatic issue generation.**

> Part of the X4 / ARIEX4Ops ecosystem — local-first, evidence-first, policy-gated autonomy.

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://python.org)
[![CI](https://github.com/dhe-cruzer69/x4-fleet/actions/workflows/nightly-audit.yml/badge.svg)](https://github.com/dhe-cruzer69/x4-fleet/actions)

One repo that replaces 30+ stub repos. Collects inventory + metrics for every repository under your account, detects staleness / CI failures / missing metadata, opens issues, and (for Level 2 repos) can propose trivial autofix PRs.

## Architecture

```
x4-fleet/
├── data/
│   ├── inventory.json          # every repo: name, purpose, status, freshness, health
│   ├── metrics/                # daily snapshots: stars, commits, CI pass rate, staleness
│   └── evidence/               # OBSERVED → VALIDATED ledger entries
├── collectors/
│   ├── gh_inventory.py         # GitHub API: full repo list, topics, CI status, issues
│   └── gh_actions_health.py    # workflow run failure detection → auto-open issue
├── healing/
│   ├── autoheal.yml            # Actions: on failure → annotate → open issue → attempt patch PR
│   └── policies.yml            # autonomy levels per repo (Level 0-3)
├── publish/
│   └── README.json             # profile README generator (auto-updates status tables)
└── .github/workflows/
    ├── nightly-audit.yml       # cron 02:00 IST: refresh inventory.json, flag staleness >7d
    └── weekly-report.yml       # Monday: commit metrics diff, open "fleet report" issue
```

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Run inventory once (requires GITHUB_TOKEN with repo + workflow scopes)
export GITHUB_TOKEN=ghp_...
python -m collectors.gh_inventory --owner dhe-cruzer69 --out data/inventory.json

# Check health
python -m collectors.gh_actions_health --inventory data/inventory.json
```

## Autonomy Levels (from X4 policy)

| Level | Name                | Allowed actions                                      |
|-------|---------------------|------------------------------------------------------|
| 0     | Observe             | Read → inspect → report                              |
| 1     | Assist              | Read → plan → patch → open PR                        |
| 2     | Governed Autopilot  | Plan → policy → execute → verify → recover / autofix |
| 3     | Never autonomous    | Delete, secrets, production destructive, financial   |

Default for new repos: **Level 0 / 1**. Level 2 only after explicit policy entry.

## Quality Gate

Nothing is "done" until:

- inventory runs green nightly
- zero repos stale >14 days
- zero failing workflows on flagship repos
- twin pairs merged
- empty stubs archived

Until then the fleet status remains **UNKNOWN**.

## Related X4 Repos

- [x4-beast](https://github.com/dhe-cruzer69/x4-beast) — control plane
- [x4-evidence](https://github.com/dhe-cruzer69/x4-evidence) — evidence ledger
- [x4-autofix](https://github.com/dhe-cruzer69/x4-autofix) — recovery loops
- [x4-sec-action](https://github.com/dhe-cruzer69/x4-sec-action) — security scanner Action

## License

Apache-2.0
