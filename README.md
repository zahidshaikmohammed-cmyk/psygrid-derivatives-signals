# PSYGRID OPTIONS ENGINE v1.0

Intraday options **signal** engine for NIFTY / BANKNIFTY / SENSEX (research and signal generation only; it never places orders).

## Status: Phase 1 (live endpoint inspection)

We build the engine from the **real** JSON schemas. Nothing downstream (schema adapter,
integrity gate, analytics, setups) gets written until those schemas are captured and documented.

### Phase 1: run the inspector (Windows PowerShell)

```powershell
cd <project-folder>
python -m pip install -r requirements.txt
python tools\inspect_endpoints.py --rounds 3 --interval 20
```

Run it **during market hours** so timestamps, freshness and changing fields are visible.
It writes:

| path | contents |
|---|---|
| `samples/raw/<run_id>/r<N>/<name>.json` | raw response body, byte-for-byte |
| `samples/raw/<run_id>/r<N>/<name>.meta.json` | HTTP status, latency, headers, network/parse error |
| `samples/schema/<run_id>/schema_report.md` | recursive schema: every observed path, types, presence counts, examples, min/max, zero/null counts, list lengths, timestamp hints, which fields changed between rounds |
| `samples/schema/<run_id>/schema.json` | the same, machine-readable |

Then commit and push `samples/`:

```powershell
git add samples
git commit -m "Add live endpoint samples"
git push
```

To re-analyse saved snapshots offline:

```powershell
python tools\inspect_endpoints.py --from-dir samples\raw\<run_id>
```

### Tests

```powershell
python -m pytest -q
```

All tests use mocked data. None of them call the live server.
