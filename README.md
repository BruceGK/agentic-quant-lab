# agentic-quant-lab

Integrity-first quantitative research, **Phase 0 only**: a prospective SEC EDGAR
filing recorder. No trading, strategies, LLM extraction, broker integration, UI,
Qlib, or agent orchestration. `ExecutionAdapter` is an empty protocol placeholder.

## Layout

- `src/agentic_quant_lab/`: configuration, SEC transport/parsers, JSONL ledger,
  PostgreSQL projection, recorder, CLI, execution placeholder.
- `migrations/`: ordered SQL migrations, applied once by a separate database owner.
- `tests/`: deterministic tests, real PostgreSQL integration tests, opt-in live SEC test.
- `.github/workflows/`: isolated CI and opt-in UTC recorder schedule.

## Local setup and the one-filing slice

Requires Python 3.12, uv, PostgreSQL 16+, and Linux/POSIX file locking.
Commands below assume the repository is the current directory; use absolute
paths for your durable ledger, migration files, and correction JSON files.

```sh
uv sync --locked --python 3.12
psql "$MIGRATION_DATABASE_URL" -v ON_ERROR_STOP=1 -f "$PWD/migrations/001_evidence.sql"
```

Apply `001_evidence.sql` **once to an empty schema**, not on each recorder run.
It is transactional; a failed migration rolls back. The runtime must use a
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
| `UNIVERSE_CIKS` | Comma-separated CIKs, normalized and snapshotted; required for batch commands |
| `CATCHUP_START` | Explicit first SEC dissemination-index date to reconcile, `YYYY-MM-DD`; required by `record` |
| `HEARTBEAT_URL` | Optional HTTPS success hook locally; required by scheduled workflow |

```sh
uv run quant-recorder ingest-one \
  https://www.sec.gov/Archives/edgar/data/320193/0000320193-24-000123.txt
uv run quant-recorder verify "$LEDGER_PATH"
# Repeating ingest-one does not fetch again or add duplicate evidence.
uv run quant-recorder record
# Explicitly rescan any historical interval; end must precede today's SEC Eastern date.
uv run quant-recorder catch-up --start 2026-09-08 --end 2026-09-09
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

The ledger is authoritative; PostgreSQL is its query projection:

1. Acquire a database advisory lock and an exclusive ledger file lock.
2. Verify the full ledger and check the database's existing hash prefix.
3. Replay any durable events that were not yet projected.
4. Preflight payloads for JSONB representability without writing evidence.
   Append canonical JSON with sequence, event ID, UTC record time, `prev_hash`
   and SHA-256; flush and `fsync` before the corresponding database transaction.
5. Insert with conflict handling. `UNIQUE(source, external_id)` prevents
   duplicate filing identities. SEC amendments have their own accession IDs.

A crash after the ledger append but before the database commit is recoverable
on the next run. A partial final line or divergent database fails closed; never
truncate or edit the ledger to make verification pass. Restore a known-good
backup and rebuild into a **new, empty migrated database/schema** with
`uv run quant-recorder replay`. A standalone `verify` checks hashes without any
database or network configuration.

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
completion checkpoint; other missing indexes, extraordinary closures, 403s
and failed fetches fail the run and suppress the success heartbeat.
Independent filings/dates are still attempted after source failures so one
unavailable submission cannot starve the rest of the universe. Ledger or
database write failures, by contrast, abort immediately.

## Scheduled operation and durability

The recorder workflow runs at minutes 7, 22, 37 and 52 of every hour **UTC**.
GitHub schedules can be delayed or dropped; reconciliation is required, not
optional. One constant concurrency group (`cancel-in-progress: false`) covers
both scheduled and manual workflow runs; database/file locks also protect CLI
writers. Interrupted runs are safe to retry.

Production activation is intentionally **off by default**:

1. Provision a dedicated Linux runner labelled `sec-recorder` with PostgreSQL
   access and a persistent, backed-up ledger directory **outside the checkout**.
   Restrict its runner group to this trusted default-branch workflow; never run
   pull-request/test jobs or other untrusted workloads on it.
2. Create the GitHub environment `sec-recorder`, restricted to the default
   branch. Add environment secrets `RECORDER_DATABASE_URL` (restricted runtime
   login) and `RECORDER_HEARTBEAT_URL`. Do not add migration credentials.
3. Set repository variables `SEC_USER_AGENT`, `UNIVERSE_CIKS`, `CATCHUP_START`,
   and absolute `LEDGER_PATH`; set repository variable `RECORDER_ENABLED=true`
   only after migrations, backups and the live SEC test succeed.
4. Configure the external hook to accept HTTPS POST JSON with `new_filings`,
   ledger `sequence` and `hash`, and alert on missing success heartbeats.
   Redirects are refused. Hook failure fails the job but does not undo evidence.

CI uses GitHub-hosted runners and disposable PostgreSQL, with **no production
secrets or environment**. Dependency installation in the recorder workflow
also occurs before production secrets are supplied to the recording step.

The JSONL chain is tamper-evident, not tamper-proof: an attacker who can rewrite
the entire chain, or remove a suffix together with the database, can defeat
unanchored verification. Keep independent immutable/off-host backups and retain
head hashes at the heartbeat receiver. The application does not provision or
verify those external backups. GitHub artifacts/cache are **not** the durable
ledger. Phase 0 verifies and loads the full ledger on startup; large-scale
segmentation/rotation is deliberately deferred.

## Validation

```sh
uv run ruff check .
uv run ruff format --check .
uv run pyright
TEST_DATABASE_URL=postgresql:///quant_test uv run pytest -m "not live_sec"
uv build
```

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
TEST_DATABASE_URL=postgresql:///quant_test \
uv run pytest -m live_sec -v
```

Tests cover prospective timestamps, duplicate-free reruns, durable first
discovery across failed fetches, ledger-before-database crash recovery,
missed-interval catch-up, failed-run checkpoint behavior, correction history,
ledger tampering/truncation, writer locks and append-only database permissions
and triggers. Live SEC results must not be substituted with a mocked response.