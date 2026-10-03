# Profile README generator notes

`x4-fleet` can emit a status table for the profile README from `data/inventory.json`.

Example snippet generation (run after inventory):

```bash
python -c "
import json
d=json.load(open('data/inventory.json'))
print('| Repo | Health | Staleness |')
print('|------|--------|-----------|')
for r in d.get('repos', [])[:10]:
    print(f\"| {r['name']} | {r.get('health','?')} | {r.get('staleness_days','?')}d |\")
"
```

Wire this into `.github/workflows/weekly-report.yml` or a dedicated publish job.
