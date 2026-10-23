# X4 Fleet Threat Model

## Assets

- Repository inventory completeness and identity.
- GitHub tokens, workflow permissions, and repository write access.
- Source commit, tested artifact, registry digest, SBOM, release manifest, and deployment receipt.
- Production configuration, SSH host identity, runtime state, and rollback state.

## Adversaries and failure modes

| Threat | Impact | Required control |
|---|---|---|
| Incomplete pagination or API denial treated as empty results | False fleet health | Propagate HTTP errors; explicit completeness metadata; fail closed |
| Stale or fabricated inventory fields | Incorrect scorecard | Validate types, timestamps, uniqueness, and provenance |
| Prompt or issue text treated as trusted instructions | Unsafe agent action | Treat external content as untrusted data; no command execution from content |
| Overprivileged GitHub token/workflow | Repository mutation or secret exposure | Least-privilege permissions; read-only defaults; protected environments |
| Dependency/action compromise | CI compromise | Pin third-party actions to reviewed full commit SHAs before protected release; update via reviewed PR |
| Artifact rebuilt after tests | Tested/published mismatch | Build once and publish the same artifact; compare independently observed digest |
| Wrong workflow-run artifact used | Provenance confusion | Verify repository, workflow identity, run ID/attempt, conclusion, source SHA, and artifact identity |
| SSH host key not trusted | Man-in-the-middle | Provision known_hosts from independently verified out-of-band host identity |
| Shell interpolation | Remote command injection | Fixed argument protocol, strict validation, no arbitrary shell fragments |
| Requested digest copied into observed field | False success receipt | Inspect actual running container and verify its image ID/digest mapping |
| Readiness only checks process liveness | Broken dependencies reported healthy | Structured readiness with database/cache health and bounded retries |
| Rollback attempted but not checked | False recovery claim | Capture prior digest, verify rollback result, and report attempted/verified/failed separately |
| Secret leakage in logs | Credential compromise | Never print raw environment or remote stderr; sanitize error summaries |
| Unreviewed auto-merge or destructive repair | Irreversible changes | Human approval; hard-stop destructive actions |

## Trust boundaries

1. GitHub repository and pull-request content.
2. CI runner and third-party actions.
3. GitHub API and workflow artifacts.
4. Container registry and attestations.
5. SSH transport and VPS.
6. Public readiness endpoint.

## Fail-closed conditions

Stop when repository identity, coverage, schema, provenance, image digest, host identity, health, or rollback outcome cannot be verified. A failed check is not converted to a warning merely to keep a pipeline green.
