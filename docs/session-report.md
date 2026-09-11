# Autonomous integrity audit — 2026-09-11

## Completed

- Independently reproduced the baseline: 83 passing tests, one skipped live test,
  clean lint/types/build. Inspected implementation, SQL, tests, configuration and workflows.
- Added full database/ledger reconciliation, semantic content/time/checkpoint verification,
  missing-row replay and independently retained head verification.
- Preserved observed eligibility, added code/config provenance, and separated optional
  raw-ingestion CIKs from versioned research-universe snapshots.
- Added explicit quarterly archive recovery without claiming daily dissemination coverage;
  additive migration `002` preserves existing evidence.
- Hardened credential-safe CLI failures and HTTPS success acknowledgement. Added local
  TLS receiver tests, explicit absent-hook status, and a separate manual acceptance gate.
- Added machine-readable constitution, the 120-hour review contract, and test-only seeded
  null/positive/leakage controls. No real alpha, broker code, trading or corporate resources.

## Validation

Commands were run from `/home/runner/work/agentic-quant-lab/agentic-quant-lab`
using the locked uv environment:

| Check | Result |
| --- | --- |
| `uv run pytest -q` with `TEST_DATABASE_URL=postgresql:///quant_test` | 128 passed, 2 live SEC tests skipped |
| `TEST_DATABASE_URL=postgresql:///quant_test uv run pytest -m "not live_sec" -q` | 128 passed, 2 deselected |
| `uv run ruff check .` | Passed |
| `uv run ruff format --check .` | Passed; 25 Python files |
| `uv run pyright` | Zero errors/warnings |
| `uv build --no-sources` | Wheel and source distribution built |
| Isolated installation of the wheel, outside the checkout, followed by `quant-recorder --help` | Passed; packaged constitution also verified |
| Both SQL migrations in disposable PostgreSQL 16 schemas | Passed, including restricted-role UPDATE/DELETE/TRUNCATE rejection and empty-schema replay |
| `quant-recorder verify` against persisted synthetic acceptance JSONL with expected sequence | Passed; inspected source, accession, all four times, content hash, chain hash and previous hash |
| Existing system PyYAML parsing of both workflow files | Passed; GitHub CI also executed successfully |
| Secret scanning before every commit | No secrets found |
| CodeQL Python and Actions analysis | Zero remaining alerts |
| Independent adversarial and security follow-up reviews | No remaining significant findings |

The integrated automated code-review backend was unavailable due to its model registry
configuration; independent review agents were used instead. CodeQL did execute. A TLS
minimum-version warning in the local test receiver was fixed and the scan rerun.

## Real-world validation

- **GitHub-hosted CI genuinely ran and passed** for code commit `d3d9846`:
  [run 34584590748, attempt 2](https://github.com/BruceGK/agentic-quant-lab/actions/runs/34584590748).
  The initially approval-gated run was successfully rerun using available GitHub permission.
  Baseline CI also passed in run `34580640969`, attempt 2.
  Independent review of all 524 final-job log lines found no exposed production
  credentials or sensitive data; no artifacts were uploaded. Node 20-to-24
  compatibility notices were non-failing warnings.
- Real PostgreSQL was exercised locally and in GitHub CI; no production database was used.
- Real TLS/HTTP requests were exercised against a controlled **local** HTTPS receiver,
  including success, rejected redirect, and server error. This is not external monitoring acceptance.
- No official SEC filing was ingested: `SEC_USER_AGENT` was absent, and the opt-in live
  acceptance tests were not run. Network availability with a real SEC contact is unverified.
- No production/manual recorder workflow or external heartbeat provider was exercised.
  The recorder workflow was not present on the default branch when checked.

## Blocked

1. **SEC contact and live acceptance:** privately export a real application/contact
   `SEC_USER_AGENT`. Choose a recent official 8-K, 10-Q or 10-K complete-submission URL
   and its dissemination-index date, then run against an isolated test database:

   ```sh
   RUN_LIVE_SEC=1 \
   TEST_SEC_URL="$OFFICIAL_SEC_SUBMISSION_URL" \
   TEST_SEC_INDEX_DATE="$DISSEMINATION_DATE" \
   TEST_DATABASE_URL=postgresql:///quant_test \
   uv run pytest -m live_sec -v
   ```

   The tests verify actual persisted bytes/timestamps/hashes, duplicate-free restart,
   and recovery with latest-feed discovery intentionally omitted. Do not substitute
   synthetic fixtures or quarterly recovery for this daily-index acceptance test.

2. **Personal durable deployment:** provision personal PostgreSQL (Supabase is optional)
   and a dedicated persistent Linux runner. Apply migrations `001` then `002` once using
   a separate owner. Provision a restricted runtime role with the README grants.
   Configure a backed-up ledger directory outside the checkout and exercise restoration
   into a fresh migrated schema. No production/Supabase resources were provisioned here.

3. **External dead-man switch:** provision an acceptance HTTPS hook and alert destination.
   Configure the recorder's `HEARTBEAT_URL`, complete a real successful recording cycle,
   confirm the received chain head, then intentionally miss the receiver's interval plus
   grace and confirm alert delivery. Retain chain heads independently of the recorder.

4. **Trusted manual GitHub acceptance:** review and merge the changes to the default
   branch; restrict the dedicated runner and `sec-recorder` environment to that workflow.
   Add environment secrets `RECORDER_DATABASE_URL` and `RECORDER_HEARTBEAT_URL`; configure
   repository variables `SEC_USER_AGENT`, `UNIVERSE_CIKS`, optional `INGEST_CIKS`,
   `CATCHUP_START`, and absolute `LEDGER_PATH`. Set `RECORDER_ACCEPTANCE_ENABLED=true`,
   dispatch **SEC recorder** on the default branch, and confirm its acceptance input.
   Keep `RECORDER_ENABLED` unset/false. No recurring activation was attempted.

5. **Future execution/compliance:** the constitution records unreviewed policies and
   unknown automated-trading permission. Complete the applicable reviews before any
   separately authorized execution phase. This does not block recording-only acceptance;
   no execution implementation is provided.

## Findings

Fixed with regression evidence:

- Hash-only database checking missed changed payloads and missing materialized rows.
- Canonical JSON byte comparison rejected intact exponent-form JSONB corrections;
  comparisons now use lossless numeric semantics without conflating booleans and numbers.
- Incomplete ingestion-scope metadata could certify a broader checkpoint than was verified.
- Provider exceptions could leak password/token fragments into CLI logs.
- Future recorder start dates and future acceptance timestamps could produce misleading
  successful/eligible state; these paths now fail visibly.
- Manual acceptance previously shared the recurring enable gate. It now has a separate
  confirmation and cannot enable scheduling; packaged policy also blocks scheduled runs.

Remaining operational limits are explicit: full-ledger startup verification is not a
large-scale segmented storage solution; response size is bounded; old indexes may need
manual archive recovery; a chain needs independent backups/head retention to resist
wholesale replacement. None was hidden by altering evidence or weakening tests.

## Commits

- `b6a4907` — full projection reconciliation, semantic verification and replay.
- `7748a29` — provenance, separate scopes, safe heartbeat/CLI and disabled scheduler policy.
- `0701c71` — archive recovery, numeric/scope fixes and stronger acceptance tests.
- `76d1b58` — seeded synthetic null/positive/leakage control fixtures.
- `d3d9846` — end-to-end acceptance CLI checks and modern TLS for heartbeat tests.

This report is a separate documentation-only increment after the verified code commits.

## Phase 0 status

**CODE COMPLETE / EXTERNAL VALIDATION REQUIRED**

Local and GitHub CI evidence supports the implemented contracts. Official SEC ingestion,
external missed-heartbeat alert delivery, and durable user-owned deployment/recovery
still require genuine acceptance; none is claimed complete.

## Scheduler status

**DISABLED.** The packaged constitution disables scheduled recording and marks external
acceptance incomplete. Repository enable gates and default-branch restrictions remain
in place. No enable variable, secret, runner or recurring deployment was provisioned.

## Next recommended task

Complete one **externally monitored, durable Phase 0 acceptance cycle**, including real
SEC catch-up, duplicate-free restart, independent ledger restoration, and a missed-run alert.
