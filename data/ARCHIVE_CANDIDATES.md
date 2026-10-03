# Archive candidates — dhe-cruzer69

**Generated:** 2026-10-03  
**Action:** Archive (preferred) or delete via GitHub UI.  
**API note:** Connected GitHub tools cannot set `archived=true`; this must be done in the UI or with a PAT that has `Administration` on each repo.

## How to archive (bulk-friendly)

1. Open each repo → **Settings** → **Danger Zone** → **Archive this repository**
2. Or use `gh` CLI with a PAT that has admin:
   ```bash
   gh api -X PATCH repos/dhe-cruzer69/REPO -f archived=true
   ```
3. Prefer **archive** over delete (keeps history + redirects).

---

## A. Empty x4-* stubs (size 0 / fleet-id style) — ARCHIVE

These match the profile README “empty x4-* stubs scheduled for removal”.

```
x4-cdn
x4-resolver
x4-gateway
x4-mesh
x4-proxy
x4-health
x4-status
x4-incident
x4-alert
x4-monitor
x4-backup
x4-migrate
x4-db
x4-batch
x4-stream
x4-event
x4-webhook
x4-sync
x4-import
x4-export
x4-report
x4-dashboard
x4-analytics
x4-usage
x4-subscription
x4-billing
x4-audit
x4-role
x4-auth
x4-identity
x4-secret
x4-config
x4-infra
x4-deploy
x4-test
x4-codegen
x4-translate
x4-summary
x4-classify
x4-recommend
x4-search
x4-feed
x4-notify
x4-scheduler
x4-queue
x4-cache
x4-trace
x4-metrics
x4-security
x4-log
x4-repair
x4-guard
x4-voice
x4-vision
x4-workflow
x4-eng
x4-docs
x4-code
x4-assist
```

**Count:** 59

---

## B. Twin long-names — ARCHIVE after merge (keep short name)

| Keep | Archive |
|------|---------|
| x4-runtime | x4-local-ai-runtime |
| x4-obs | x4-agent-observability |
| x4-skills | x4-agent-skills-hub |
| x4-mcpgen | x4-mcp-server-starter |
| x4-sec | x4-ai-security-scanner |

**Count:** 5

---

## C. Low-signal public noise — ARCHIVE (optional)

```
reimagined-potato
curly-pancake
glowing-parakeet
auto-fix-todo-test
abhia
abhiachar126-s
project-scaffold
workflow-lab
```

**Count:** 8

---

## D. Private junk (review before archive)

Examples seen in inventory (private; confirm empty/unused):

```
Status
MCPl
MCPe
Actions9
Actions2
Actions
Actions-2
Repository69
Projects69
GraphQL
github
Repository
Copilot
Master
CLI
specifically
Importer
provides
abhia1
flow
astro-blog-starter-template
```

Also review: `x4-claw-` (private; fix CI or archive), monorepo experiments (`nx-monorepo`, `turbo-monorepo`, etc.).

---

## DO NOT archive (KEEP)

All polished short-name X4 family, all `ariexcore-*`, `x4-fleet`, `x4-beast`, `x4-agents`, `x4-approval`, `x4-evidence`, `x4-autofix`, `x4-sec-action`, profile `dhe-cruzer69`, and any repo with real code/stars/active CI.

---

## Suggested order

1. Section A (empty stubs) — safe
2. Section B (twins) — after optional history merge
3. Section C (noise)
4. Section D (private) — case by case

After archiving, re-run `x4-fleet` inventory to confirm `empty_stubs` → 0.
