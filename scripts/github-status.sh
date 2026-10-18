#!/usr/bin/env bash
# Read-only GitHub portfolio status report.
# Requirements: gh, jq, curl. No repository mutations.
set -Eeuo pipefail
OWNER="dhe-cruzer69"
BASE_URL="https://x4-beast-demo.onrender.com/healthz"

die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
command -v gh >/dev/null 2>&1 || die "GitHub CLI (gh) is required."
command -v jq >/dev/null 2>&1 || die "jq is required."
gh auth status >/dev/null 2>&1 || die "GitHub CLI is not authenticated."
LOGIN="$(gh api user --jq '.login')" || die "Unable to read authenticated GitHub login."
[[ "$LOGIN" == "$OWNER" ]] || die "Authenticated as '$LOGIN', expected '$OWNER'."

STAMP="$(date -u +%FT%TZ)"
printf 'X4 APEX GitHub status — %s\nOwner: %s\n\n' "$STAMP" "$OWNER"

# GitHub CLI emits one JSON array per page; slurp and flatten before counting.
REPOS_JSON="$(gh api --paginate "/user/repos?per_page=100&affiliation=owner" --jq '.[] | {name,owner:.owner.login,private,archived,default_branch}' | jq -s '[.[] | select(.owner == "'"$OWNER"'")]')" || die "Repository inventory API call failed."
TOTAL="$(jq 'length' <<<"$REPOS_JSON")"
PUBLIC="$(jq '[.[] | select(.private == false)] | length' <<<"$REPOS_JSON")"
PRIVATE="$(jq '[.[] | select(.private == true)] | length' <<<"$REPOS_JSON")"
ARCHIVED="$(jq '[.[] | select(.archived == true)] | length' <<<"$REPOS_JSON")"
printf 'Repositories: %s\nPublic: %s\nPrivate: %s\nArchived: %s\n\n' "$TOTAL" "$PUBLIC" "$PRIVATE" "$ARCHIVED"

printf '%s\n' '--- Workflow-hub gate ---'
if gh api "repos/$OWNER/x4-spec/contents/.github/workflows/reusable-python-ci.yml?ref=v1" >/dev/null 2>&1; then
  echo 'x4-spec@v1: resolvable'
else
  echo 'x4-spec@v1: NOT RESOLVABLE (do not reference until repaired)'
fi
if gh api "repos/$OWNER/x4-mcp/contents/docs/ARCHITECTURE.md" >/dev/null 2>&1; then
  echo 'x4-mcp composite architecture: present'
else
  echo 'x4-mcp composite architecture: not on default branch or not accessible'
fi
printf '\n%s\n' '--- Latest workflow evidence (no workflow is assumed to be named ci.yml) ---'
for repo in x4-core x4-beast x4-fleet x4-sandbox x4-agents x4-agent-skills-hub x4-ai-security-scanner x4-agent-observability; do
  row="$(gh run list -R "$OWNER/$repo" --limit 1 --json workflowName,name,conclusion,status,createdAt,headSha 2>/dev/null | jq -r 'if length == 0 then "no_runs" else .[0] | [.workflowName // .name // "unknown", .status // "unknown", .conclusion // "none", .createdAt // "unknown", .headSha // "unknown"] | @tsv end' || printf 'error')"
  printf '%-28s %s\n' "$repo" "$row"
done

printf '\n%s\n' '--- Source/test/release signal tally (metadata only; not a quality verdict) ---'
APEX=0; PROOF=0; REPAIR=0; UNKNOWN=0
while IFS= read -r repo; do
  [[ -n "$repo" ]] || continue
  has_src=no; has_tests=no; has_release=no
  gh api "repos/$OWNER/$repo/contents/src" >/dev/null 2>&1 && has_src=yes
  gh api "repos/$OWNER/$repo/contents/tests" >/dev/null 2>&1 && has_tests=yes
  release="$(gh release list -R "$OWNER/$repo" --limit 1 --json tagName --jq '.[0].tagName // empty' 2>/dev/null || true)"
  [[ -n "$release" ]] && has_release=yes
  if [[ "$has_src" == yes && "$has_tests" == yes && "$has_release" == yes ]]; then APEX=$((APEX+1))
  elif [[ "$has_src" == yes && "$has_tests" == yes ]]; then PROOF=$((PROOF+1))
  elif [[ "$has_src" == yes ]]; then REPAIR=$((REPAIR+1))
  else UNKNOWN=$((UNKNOWN+1))
  fi
done < <(jq -r '.[] | select(.private == false and .archived == false) | .name' <<<"$REPOS_JSON")
printf 'APEX signal (src+tests+release): %s\nPROOF signal (src+tests): %s\nREPAIR signal (src only): %s\nUNKNOWN signal: %s\n' "$APEX" "$PROOF" "$REPAIR" "$UNKNOWN"

printf '\n%s\n' '--- Demo health probe ---'
if health="$(curl -fsS --max-time 5 "$BASE_URL" 2>/dev/null)"; then
  if jq -e '.status == "ok"' >/dev/null 2>&1 <<<"$health"; then
    printf 'x4-beast demo: health endpoint responded with status=ok at %s\n' "$BASE_URL"
  else
    printf 'x4-beast demo: reachable but health payload did not assert status=ok\n'
  fi
else
  printf 'x4-beast demo: not reachable or timeout at %s\n' "$BASE_URL"
fi
printf '\nNo repository mutations performed by this script. Timestamp: %s\n' "$STAMP"
