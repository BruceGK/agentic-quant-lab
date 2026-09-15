# agentic-quant-lab

Integrity-first quantitative research, **Phase 0 only**: a prospective SEC EDGAR
filing recorder. No trading, strategies, LLM extraction, broker integration, UI,
Qlib, or agent orchestration. `ExecutionAdapter` is an empty protocol placeholder.

## Layout

- `src/agentic_quant_lab/`: configuration, SEC transport/parsers, local/Blob ledger,
  PostgreSQL projection, recorder, CLI, execution placeholder.
- `migrations/`: ordered SQL migrations, applied once by a separate database owner.
- `tests/`: deterministic tests, real PostgreSQL integration tests, opt-in live SEC test.
- `.github/workflows/`: isolated CI and manual-only Azure recorder automation.
- `infra/azure/`: reproducible Azure deployment, isolated database roles and monitoring.
- `Dockerfile`: pinned, non-root production image without development/build tools.

## Local setup and the one-filing slice

Requires Python 3.12, uv, PostgreSQL 16+, and Linux/POSIX file locking.
Commands below assume the repository is the current directory; use absolute
paths for your durable ledger, migration files, and correction JSON files.

```sh
uv sync --locked --python 3.12
psql "$MIGRATION_DATABASE_URL" -v ON_ERROR_STOP=1 -f "$PWD/migrations/001_evidence.sql"
psql "$MIGRATION_DATABASE_URL" -v ON_ERROR_STOP=1 -f "$PWD/migrations/002_archive_recovery.sql"
```

Apply migrations in numeric order **once**, not on each recorder run.
Existing `001` installations apply only `002`; it permits archive recovery
events without changing prior evidence. Each migration is transactional.
The runtime must use a
separate non-owner, non-superuser login with only `CONNECT` on the database,
`USAGE` on the schema and `SELECT, INSERT` on the evidence tables. A database
administrator must provision that login and its authentication out of band.
For an existing login named `quant_recorder` and a database named `quant_lab`:

```sql
GRANT CONNECT ON DATABASE quant_lab TO quant_recorder;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO quant_recorder;
GRANT SELECT, INSERT ON audit_events, discoveries, filings, corrections TO quant_recorder;
GRANT SELECT ON universe_snapshots, reconciliations TO quant_recorder;
```

Do not grant schema/table ownership, role membership in the migration owner,
`CREATE`, `UPDATE`, `DELETE`, `TRUNCATE`, or replication/trigger-disabling
privileges. Triggers additionally reject UPDATE/DELETE/TRUNCATE, including
TRUNCATE CASCADE, even for ordinary owner-issued statements. A superuser or
owner able to drop objects or disable triggers is outside this protection boundary.

Set configuration in your shell or secret manager; `.env` files are not loaded.
Never commit credentials.

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Runtime PostgreSQL DSN; use certificate-verified TLS for remote production databases |
| `SEC_USER_AGENT` | Required application name and real contact email, per SEC fair-access policy |
| `LEDGER_PATH` | Durable JSONL path; defaults to `state/sec.jsonl` for local development only |
| `LEDGER_BACKEND` | `local` (default) or `azure`; Azure never uses the local path as a durability fallback |
| `AZURE_STORAGE_ACCOUNT_URL` | HTTPS Blob account endpoint without credentials/query/path; required for Azure |
| `AZURE_STORAGE_CONTAINER` / `AZURE_LEDGER_PREFIX` | Isolated ledger namespace; defaults `aql-audit-ledger` / `sec` |
| `DATABASE_AUTH` | `password` (existing local behavior) or `azure` (short-lived Entra token) |
| `AZURE_SUBSCRIPTION_ID` | Explicit subscription for local Azure CLI authentication |
| `AZURE_CLIENT_ID` | Explicit user-assigned managed identity in Container Apps |
| `UNIVERSE_CIKS` | Comma-separated CIKs, normalized and snapshotted; required for batch commands |
| `INGEST_CIKS` | Optional separate raw-ingestion scope; defaults to the research universe for a bounded deployment |
| `CATCHUP_START` | Explicit first SEC dissemination-index date to reconcile, `YYYY-MM-DD`; required by `record` |
| `HEARTBEAT_URL` | Optional HTTPS success hook locally; required by scheduled workflow |
| `RECORDER_GIT_SHA` | Optional full code commit SHA; set automatically by the workflow |

```sh
uv run quant-recorder ingest-one \
  https://www.sec.gov/Archives/edgar/data/320193/0000320193-24-000123.txt
uv run quant-recorder verify "$LEDGER_PATH"
# Repeating ingest-one does not fetch again or add duplicate evidence.
uv run quant-recorder record
# Explicitly rescan any historical interval; end must precede today's SEC Eastern date.
uv run quant-recorder catch-up --start 2026-09-08 --end 2026-09-09
# Explicit tertiary recovery for a completed quarter whose daily indexes are unavailable:
uv run quant-recorder recover-quarter --year 2024 --quarter 4
```

Use a complete SEC submission `.txt` URL, not its primary HTML document. The
recorder archives the exact bytes as base64 in the ledger, plus their SHA-256.
HTTP requests identify the caller, are bounded to 32 MiB and 45 seconds, use
at most four attempts, and are paced to at most four requests/second, below the
[SEC's ten-request/second limit](https://www.sec.gov/about/developer-resources).
Coordinate this budget with any other clients sharing the same IP.
Oversized, malformed, blocked, or incomplete responses fail without publishing
eligible content. Large submissions need an explicitly reviewed size-limit
change, not truncation.

## Evidence and time contract

All stored timestamps are timezone-aware UTC:

| Field | Meaning |
| --- | --- |
| `accepted_at` | `<ACCEPTANCE-DATETIME>` from the SEC submission header, converted from America/New_York with DST |
| `first_seen_at` | Our first discovery, durably appended before attempting the content fetch |
| `fetched_at` | When a complete successful content fetch returned |
| `decision_eligible_at` | Exactly `fetched_at`, including filings recovered through catch-up |

SEC acceptance and index filing dates are **not** observation times. Historical
catch-up never pretends the content was available to this system earlier.
Ambiguous/nonexistent local acceptance times fail closed rather than guessing.
The host clock must be synchronized. Failed fetches retain their discovery
timestamp across retries and restarts.
New filing payloads explicitly carry `availability_mode=observed`; legacy
records have the same enforced observed semantics, not inferred availability.
Every new event carries package version, a hash of package source/config files,
optional Git SHA, and a nonsecret recorder configuration with its own hash.
No contact identities, DSNs, heartbeat URLs, or credential hashes are recorded
as provenance. Old evidence is not rewritten to fill missing provenance.

The ledger is authoritative; PostgreSQL is its query projection:

1. Acquire a database advisory lock and, locally, an exclusive ledger file lock.
2. Verify the full hash chain, content hashes, identities, prospective timestamps,
   and checkpoint prerequisites; compare every existing database row and payload.
3. Replay missing durable events and missing materialized rows without modifying
   any existing evidence. Divergence fails closed before repair.
4. Preflight payloads for JSONB representability without writing evidence.
   Append canonical JSON with sequence, event ID, UTC record time, `prev_hash`
   and SHA-256; flush and `fsync` (local) or atomically commit a create-only
   block blob (Azure) before the corresponding database transaction.
5. Insert with conflict handling. `UNIQUE(source, external_id)` prevents
   duplicate filing identities. SEC amendments have their own accession IDs.

A crash after the ledger append but before the database commit is recoverable
on the next run. A partial final line or divergent database fails closed; never
truncate or edit the ledger to make verification pass. Restore a known-good
backup and rebuild into a **new, empty migrated database/schema** with
`uv run quant-recorder replay`. A standalone `verify` checks chain and evidence
semantics without database/network configuration. `uv run quant-recorder reconcile`
detects missing, extra, or differing database evidence **without repairing it**;
`replay` inserts only missing rows after verifying all existing rows match.
Successful recording/catch-up reconciles again before sending any healthy heartbeat.
Offline `verify`, `reconcile`, and `replay` need no SEC contact identity.
An independent heartbeat/backup head can be checked with:
`quant-recorder verify "$LEDGER_PATH" --expected-sequence N --expected-head HASH`.

Corrections are new linked events, not edits or silent replacements:

```sh
uv run quant-recorder correct EVENT_UUID --reason "Explanation" \
  --changes /absolute/path/to/annotation.json
```

The JSON object is an explicit annotation/change proposal; the original filing
and its timestamps stay unchanged. Query `corrections` alongside original
evidence rather than treating annotations as retroactively available facts.
An identical target/reason/changes correction is idempotent.

## Discovery, reconciliation, and universe snapshots

The latest-filings Atom feed is a low-latency hint with only 100 entries, not a
complete history. Each successful `record` also scans daily master indexes
from `CATCHUP_START` through yesterday in SEC Eastern time. Only selected CIKs
are fetched. Daily checkpoints are appended **after all selected filings are
persisted**, scoped to the universe hash, and include the exact index bytes and
hash. Older completed dates are skipped; the latest three completed dates are
rechecked for late index publication. Explicit `catch-up` forces a rescan.
The index header's dissemination date must match the requested day; individual
rows can legitimately have older filing dates. Declared HTTP content lengths
are checked before any response can become reconciliation evidence.

Missing intervals, failed fetches, and changed universes are therefore
recoverable without backdating eligibility. Universe changes append a new
snapshot and trigger reconciliation for the new scope; they never delete
earlier evidence. Pending discoveries remain eligible for retry even if a CIK
is later removed. SEC indexes can be republished; rescan older dates explicitly
if necessary. A 404 on a known weekend/federal holiday is allowed without a
completion checkpoint. SEC also returns 403 for some nonexistent weekend objects:
only on a known closure, a successfully fetched and validated official quarter
directory proving that exact index absent permits skipping it without a checkpoint.
Listed-but-inaccessible indexes, weekday 403s, malformed/unavailable directories,
other unexplained missing indexes, extraordinary closures and failed fetches
fail the run and suppress the success heartbeat.
Independent filings/dates are still attempted after source failures so one
unavailable submission cannot starve the rest of the universe. Ledger or
database write failures, by contrast, abort immediately.
Snapshots include an observed `as_of`, explicit-list screen version, config
hash, and selection reason. Membership is a step function of snapshots in
ledger order; before the first snapshot it is **unknown**, not today's list.
Only listed CIKs are eligible under that snapshot. `INGEST_CIKS` can record a
broader raw scope without granting research eligibility. Checkpoints bind the
ingestion scope independently; expanding it reopens historical reconciliation.

## Azure deployment and durability

See [the Azure runbook](infra/azure/README.md) for reproducible deployment and
real-world acceptance, and [the deployment report](docs/azure-deployment-report.md)
for actual resources, costs, tests and remaining gates. It reuses discovered shared
infrastructure without redeploying RiskPulse applications. PostgreSQL and the Blob namespace are
isolated AQL state. The production container has no build/development tools,
runs as a non-root user, and performs no dependency installation at startup.

The [real SEC acceptance report](docs/sec-acceptance-report.md) records successful
official ingestion, prospective timestamps, duplicate-free reruns, missed-interval
recovery and independent filing-bearing replay. This is manual acceptance only;
the scheduler and live-execution policy remain disabled.

Azure uses managed identity for Blob and PostgreSQL. A separate Entra
migration administrator owns the schema; the recorder has only the evidence
grants described above. `DATABASE_AUTH=azure` requires a password-free DSN
to an Azure PostgreSQL endpoint with `sslmode=verify-full` and a trusted
`sslrootcert`. Local Azure commands use the explicitly selected subscription;
Container Apps uses the explicitly configured runtime identity.

The Blob backend stores one canonical JSONL record per block blob:
`sec/records/00000000000000000001.jsonl`, and so on. Atomic create-if-absent
commits prevent two writers from replacing the same sequence, including
writers attached to different databases. Large SEC records are not constrained
by the legacy append-blob 4 MiB limit. Upload failure, an ambiguous acknowledgement,
gaps, unexpected filenames, or invalid bytes fail closed. A subsequent verified
replay recovers a committed Blob record whose database transaction was missed.
There is no local-file fallback and no mutable head/manifest to reconcile.
All records are re-read and verified before reporting database reconciliation.
As with the local backend, full-chain scans are intentionally Phase 0 scale.

Independent verification and export need neither a database nor SEC contact:

```sh
# Configure LEDGER_BACKEND=azure and the nonsecret Azure endpoint/identity settings.
uv run quant-recorder verify-blob
uv run quant-recorder export-ledger /absolute/backup/sec.jsonl \
  --expected-sequence N --expected-head HASH
uv run quant-recorder verify /absolute/backup/sec.jsonl \
  --expected-sequence N --expected-head HASH
# Point DATABASE_URL at a NEW, empty migrated restore database/schema.
LEDGER_BACKEND=local LEDGER_PATH=/absolute/backup/sec.jsonl uv run quant-recorder replay
LEDGER_BACKEND=local LEDGER_PATH=/absolute/backup/sec.jsonl uv run quant-recorder reconcile
```

Export refuses to overwrite an existing destination. Retain the expected head
independently, not just beside the ledger being checked. Azure storage enables
versioning and soft delete, not irreversible WORM retention.

## Manual execution and success monitoring

**Scheduling remains disabled.** The Azure Job has a `Manual` trigger, the
GitHub recorder workflow has no cron trigger, and the packaged constitution
still prohibits scheduled recording and live execution. A manually dispatched
workflow uses scoped GitHub OIDC, not the operator's Azure CLI login or a
long-lived client secret. CI stays on GitHub-hosted runners with disposable
PostgreSQL and **no production secrets or Azure identity**.

Supply the real `SEC_USER_AGENT` through the job's secret configuration, never
the image, committed parameters, or test CI. Missing contact fails recording
without fabricating evidence. `snapshot`, `verify-blob`, `reconcile`, and
`replay` remain available without it but do not satisfy SEC acceptance.

The recorder emits `event=aql.recorder.completed` only after `record` or
`catch-up` has completed ingestion, durable ledger writes, database commits,
and final reconciliation. Azure Monitor additionally requires
`ledger_backend=azure` and `reconciliation=passed`. Merely starting a process,
a successful maintenance command, or an Azure Job `Succeeded` status is not
an ingestion heartbeat. Failed recording/reconciliation exits nonzero with
fixed credential-free JSON error codes. Provider exception messages and
tracebacks are deliberately not printed.

An optional local `HEARTBEAT_URL` still accepts HTTPS POST JSON containing
`new_filings`, `sequence`, and `hash`. Redirects are refused; only a 2xx
acknowledgement succeeds, and hook failure fails the job without undoing
evidence. Omission is explicit (`heartbeat=disabled`). Azure log alerts provide
the deployment's independent failure/dead-man path without requiring this hook.

Quarterly archive recovery is manual and uses SEC's `full-index` master index.
It records exact index bytes and a distinct `archive_recovery` event only after
the selected content is persisted. It **never** advances daily reconciliation
checkpoints: quarterly filing dates cannot prove daily dissemination coverage.
Eligibility remains observed at the actual fetch, and oversized archives fail
the same bounded-download policy instead of silently truncating.

The JSONL chain is tamper-evident, not tamper-proof: an attacker who can rewrite
the entire chain, or remove a suffix together with the database, can defeat
unanchored verification. Keep independent immutable/off-host backups and retain
head hashes at the heartbeat receiver or in independently retained Azure logs.
Blob versions/soft delete are recoverability aids, not proof against an
administrator rewriting all history. Demonstrate export and replay into a
fresh database before claiming restoration acceptance. GitHub artifacts/cache
are **not** the durable ledger. Phase 0 verifies and loads the full ledger on startup; large-scale
segmentation/rotation is deliberately deferred.

## Validation

```sh
uv run ruff check .
uv run ruff format --check .
uv run pyright
TEST_DATABASE_URL=postgresql:///quant_test uv run pytest -m "not live_sec and not live_azure"
uv build
```

The production image is also built and smoke-tested in CI, without an Azure
identity or production configuration. The opt-in Azure persistence test uses
a generated, isolated `acceptance/<uuid>` Blob prefix and the usual disposable
PostgreSQL schema. It tests real conditional commits, independent export and
idempotent replay, but deliberately creates **no SEC filing evidence**:

```sh
RUN_LIVE_AZURE=1 \
TEST_AZURE_STORAGE_ACCOUNT_URL=https://YOURACCOUNT.blob.core.windows.net \
TEST_AZURE_STORAGE_CONTAINER=aql-audit-acceptance \
TEST_DATABASE_URL=postgresql:///quant_test \
uv run pytest tests/test_live_azure.py -v
```

It requires explicit `AZURE_SUBSCRIPTION_ID`, an authenticated local Azure CLI,
and Blob read/write/delete permission on that isolated test container. Only its generated
test blobs are removed; production `sec/` records are never touched.

Use only an **isolated disposable test database** whose test administrator can
create roles and schemas. Each PostgreSQL test gets a separate schema and
restricted writer role. Without `TEST_DATABASE_URL`, database tests skip;
CI always supplies it. Unit fixtures are explicitly synthetic, not proof of
real SEC connectivity.

The real-filing acceptance gate is opt-in and must pass before calling Phase 0
operationally complete. Use your real SEC contact User-Agent, a network allowed
by SEC, and the isolated test database (no production secrets):

```sh
RUN_LIVE_SEC=1 \
TEST_SEC_URL=https://www.sec.gov/Archives/edgar/data/320193/0000320193-24-000123.txt \
TEST_SEC_INDEX_DATE=2024-11-01 \
TEST_DATABASE_URL=postgresql:///quant_test \
uv run pytest -m live_sec -v
```

Tests cover prospective timestamps, duplicate-free reruns, durable first
discovery across failed fetches, ledger-before-database crash recovery,
missed-interval catch-up, failed-run checkpoint behavior, correction history,
ledger tampering/truncation, writer locks and append-only database permissions
and triggers. Live SEC results must not be substituted with a mocked response.
The live tests require both the filing URL and its dissemination-index date;
they verify original bytes/hashes and timestamps, a restart with zero duplicates,
and recovery with latest-feed discovery deliberately omitted. If SEC has retired
that daily index, choose a recent 8-K/10-Q/10-K with an available daily index;
manual quarterly recovery is not a substitute for the daily-catch-up acceptance gate.

To inspect a separately provisioned acceptance recorder after a real run:

```sh
uv run quant-recorder reconcile
uv run quant-recorder verify "$LEDGER_PATH"
psql "$DATABASE_URL" -c \
  'SELECT source, external_id, accepted_at, first_seen_at, fetched_at,
          decision_eligible_at, content_sha256 FROM filings ORDER BY fetched_at DESC LIMIT 5'
psql "$DATABASE_URL" -c \
  'SELECT sequence, kind, prev_hash, record_hash FROM audit_events ORDER BY sequence DESC LIMIT 5'
```

Use a dedicated acceptance heartbeat endpoint. Confirm receipt of the successful
run's chain head, then deliberately stop manual acceptance runs and wait past
the receiver's configured interval plus grace; verify an alert reaches you.
This tests the external dead-man switch, not merely HTTP delivery. Do not send
standalone synthetic successes to a production monitoring endpoint.

## 120-hour review contract

The packaged machine-readable constitution sets a six-hour weekly budget and
a review at 120 total hours. Expected deliverables by that review are:
a reliable prospective recorder, externally monitored ingestion, an independently
recoverable ledger, a point-in-time data contract, an immutable experiment-registry
foundation, validated null/positive/leakage controls, first panel-evidence
implementation, first published-anomaly replication, and an analytic feasibility map.
These are review targets, **not claims of current completion**.

Outside that scope: autonomous live trading, production Robinhood execution,
multi-agent trading swarms, polished UI, RD-Agent integration, and sophisticated
automated strategy discovery. Compliance status remains unreviewed/unknown;
live execution cannot be enabled before the required policy reviews and explicit
authorization of a future phase. No broker implementation exists here.

## Synthetic scientific controls (test-only)

`tests/scientific_controls.py` contains immutable, seeded IID linear fixtures and
a toy slope estimator with normal-approximation uncertainty. Tests across a
fixed seed ensemble check a null random score, recovery of a known planted
effect, interval coverage/standard-error calibration, and rejection of deliberately
future-available information. Generator version and seed identify the fixtures.
Run `uv run pytest tests/test_scientific_controls.py`.

This is only a Phase 1 control foundation: no market downloads, real anomalies,
Sharpe ratios, experiment registry, or panel-evidence implementation. Passing IID
control tests does not establish uncertainty calibration for dependent market data.