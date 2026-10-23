from __future__ import annotations
import json, re, sys
from datetime import datetime
from pathlib import Path
from typing import Any
DIGEST_RE = re.compile(r'^sha256:[0-9a-f]{64}$')
COMMIT_RE = re.compile(r'^(?:[0-9a-f]{40}|[0-9a-f]{64})$')
IMAGE_RE = re.compile(r'^ghcr\.io/[a-z0-9]+(?:[._-][a-z0-9]+)*/[a-z0-9]+(?:[._-][a-z0-9]+)*(?:/[a-z0-9]+(?:[._-][a-z0-9]+)*)*$')
UTC_RE = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$')
REQUIRED = {'schema_version','repository','commit_sha','workflow_run_id','workflow_attempt','image','image_digest','sbom_digest','quality_status','security_status','integration_status','created_at_utc'}
def valid_utc(value: Any) -> bool:
    if not isinstance(value, str) or not UTC_RE.fullmatch(value): return False
    try: datetime.fromisoformat(value[:-1] + '+00:00')
    except ValueError: return False
    return True
def validate_manifest(data: Any) -> list[str]:
    if not isinstance(data, dict): return ['manifest root must be an object']
    errors=[]; missing=REQUIRED-data.keys(); extra=data.keys()-REQUIRED
    if missing: errors.append('missing fields: '+', '.join(sorted(missing)))
    if extra: errors.append('unknown fields: '+', '.join(sorted(extra)))
    if errors: return errors
    for f in ('schema_version','repository','commit_sha','image','image_digest','sbom_digest','quality_status','security_status','integration_status','created_at_utc'):
        if type(data[f]) is not str: errors.append(f'{f} must be a string')
    for f in ('workflow_run_id','workflow_attempt'):
        if type(data[f]) is not int or data[f] < 1: errors.append(f'{f} must be a positive integer')
    if errors: return errors
    if data['schema_version'] != '1': errors.append('unsupported schema_version')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', data['repository']): errors.append('invalid repository identity')
    if not COMMIT_RE.fullmatch(data['commit_sha']): errors.append('invalid commit_sha')
    if not IMAGE_RE.fullmatch(data['image']): errors.append('invalid image repository')
    for f in ('image_digest','sbom_digest'):
        if not DIGEST_RE.fullmatch(data[f]): errors.append(f'invalid {f}')
    for f in ('quality_status','security_status','integration_status'):
        if data[f] != 'PASS': errors.append(f'{f} must be PASS')
    if not valid_utc(data['created_at_utc']): errors.append('created_at_utc must be a valid RFC3339 UTC timestamp ending in Z')
    return errors
def main(argv: list[str] | None = None) -> int:
    args=sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print('Usage: python scripts/verify_release.py <manifest.json>', file=sys.stderr); return 2
    try: data=json.loads(Path(args[0]).read_text(encoding='utf-8'))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f'ERROR: cannot read manifest ({type(exc).__name__})', file=sys.stderr); return 1
    errors=validate_manifest(data)
    if errors:
        for error in errors: print(f'ERROR: {error}', file=sys.stderr)
        return 1
    print(f"Manifest schema checks passed: {data['image']}@{data['image_digest']}")
    print('NOTE: schema validation does not prove gates or provenance; verify those independently.')
    return 0
if __name__ == '__main__': raise SystemExit(main())
