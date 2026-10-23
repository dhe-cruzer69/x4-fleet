from __future__ import annotations
import re
from datetime import datetime
from typing import Any
D = re.compile(r'^sha256:[0-9a-f]{64}$')
T = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$')
def validate_receipt(data: Any) -> list[str]:
    if not isinstance(data, dict): return ['receipt root must be an object']
    required = {'schema_version','deployment_id','release_run_id','target','status','requested_digest','observed_digest','source_commit','started_at_utc','finished_at_utc','readiness','rollback'}
    errors=[]
    if required-data.keys(): errors.append('missing required fields')
    if data.keys()-(required|{'error'}): errors.append('unknown fields')
    for f in ('started_at_utc',):
        v=data.get(f)
        if not isinstance(v,str) or not T.fullmatch(v): errors.append(f'{f} must be RFC3339 UTC')
        else:
            try: datetime.fromisoformat(v[:-1]+'+00:00')
            except ValueError: errors.append(f'{f} is not a valid timestamp')
    if data.get('status') == 'succeeded':
        a,b=data.get('requested_digest'),data.get('observed_digest')
        if not isinstance(a,str) or not D.fullmatch(a): errors.append('invalid requested_digest')
        if not isinstance(b,str) or not D.fullmatch(b): errors.append('invalid observed_digest')
        if isinstance(a,str) and isinstance(b,str) and a != b: errors.append('requested_digest must equal observed_digest for succeeded receipts')
        if not isinstance(data.get('readiness'),dict): errors.append('succeeded receipt requires readiness evidence')
        v=data.get('finished_at_utc')
        if not isinstance(v,str) or not T.fullmatch(v): errors.append('succeeded receipt requires finished_at_utc')
    rb=data.get('rollback')
    if isinstance(rb,dict):
        state,attempted=rb.get('status'),rb.get('attempted')
        if state == 'not_attempted' and attempted is not False: errors.append('not_attempted rollback must have attempted=false')
        if state in {'attempted','verified','failed'} and attempted is not True: errors.append('attempted rollback states require attempted=true')
        if state == 'verified' and not isinstance(rb.get('observed_digest'),str): errors.append('verified rollback requires observed_digest')
    else: errors.append('rollback must be an object')
    return errors
