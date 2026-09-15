# Real SEC Phase 0 acceptance - 2026-09-15

**External acceptance: PASS for the deployed Phase 0 recorder. Scheduling: DISABLED.**

This supersedes the SEC-contact blockers in the
[initial deployment report](azure-deployment-report.md). No SEC contact value was
retrieved, printed, copied locally, placed in source/build arguments, or returned
by an operator command. The job alone consumes the existing secret when requesting SEC.

All Azure operations targeted subscription
`ccc5a11c-86d7-40f1-b02c-58660a2582a7`.

## Secret mapping and runtime-only deployment

The existing job contained a secret named `sec-user-agent`, but initially had no
`SEC_USER_AGENT` environment mapping. Ordinary job metadata, not `listSecrets`,
established that mismatch.

The persisted mapping is now:

```text
SEC_USER_AGENT -> secretRef: sec-user-agent
triggerType   -> Manual
```

The [runtime Bicep](../infra/azure/runtime.bicep) and
[deployment helper](../infra/azure/scripts/deploy.py) now support
`useExistingSecUserAgentSecret=true`.

Azure what-if showed that a full job PUT omitting the secret collection would
delete it. That plan was **not applied**. Instead, Bicep resolves the nonsecret
desired runtime, and the helper applies its configuration/template through PATCH,
without a `secrets` collection. The helper checks the reference and requested image
after deployment. Reference-only mode does not even read a local `SEC_USER_AGENT`.

Only the AQL runtime was redeployed. PostgreSQL, Blob, networking, monitoring,
RiskPulse resources, role grants and scheduling were not broadened or reprovisioned.
The updated image was built in the already reused ACR from an immutable commit.

## Real SEC compatibility issue found and corrected

The first actual recording execution, `aql-recorder-xhosati`, persisted an official
filing and the September 10-11 daily checkpoints, then correctly failed the overall
run when SEC returned **403** for the September 12-13 weekend index URLs.

Bounded in-job diagnostics established:

- The latest feed parsed 100 entries.
- September 10 and 11 official master indexes downloaded and parsed successfully.
- The official filing bytes downloaded and passed the existing identity/header parser.
- Both weekend index URLs returned 403 rather than 404.
- The official quarter `index.json` directory identified itself as
  `daily-index/2026/QTR3/`, contained 255 entries, and did not list those weekend files.

The corrected [SEC client](../src/agentic_quant_lab/sec.py) tolerates this response
**only** for a known scheduled closure and only after a bounded, successful,
validated official quarter listing proves the exact master index absent.
Weekday 403s, listed-but-inaccessible files, malformed/wrong/empty directories and
directory transport failures still fail closed. No fake daily completion checkpoint
is created for a closure. Existing evidence was never rewritten.

## Official filing and prospective timestamps

Production PostgreSQL and the independently verified Blob ledger agree on:

| Field | Verified value |
| --- | --- |
| Source | `sec` |
| CIK | `320193` |
| Accession / external ID | `0001140361-26-036226` |
| `accepted_at` | `2026-09-10T22:30:31+00:00` |
| `first_seen_at` | `2026-09-14T18:45:51.626131+00:00` |
| `fetched_at` | `2026-09-14T18:45:51.841876+00:00` |
| `decision_eligible_at` | `2026-09-14T18:45:51.841876+00:00` |
| Content SHA-256 | `1ac93a18c848efcc4a8ccdd612e176bbddf2637e1e3c65cb147b7c95f3d97917` |
| Filing record hash | `ed2e10452d8129958091e0ea0309e3757fa1a157fca47b89acfa8d592102004f` |
| Filing previous hash | `6202af2aadfb293364b7c94919addcde5300683969c72fc71ef9732b55a2d305` |

Eligibility is the actual successful fetch time, not the earlier SEC acceptance
time. An independent recovery later fetched the same bytes with a **later**
first-seen/fetched/eligible time, not backdated availability.

## Real executions and idempotence

| Execution | Actual operation | Result |
| --- | --- | --- |
| `aql-recorder-xhosati` | Initial official ingestion and daily recovery | Filing/checkpoints durable; overall run failed on weekend 403 |
| `aql-recorder-fourud2` | Repeat official September 10-11 catch-up | Succeeded; zero new filings, unchanged sequence 5/head |
| `aql-recorder-lrlijyp` | Deliberately missed interval in isolated Azure projection | Recovered one official filing, then zero on rerun |
| `aql-recorder-zzfl1n2` | Full `record` with corrected image | Succeeded; `aql.recorder.completed`, Azure ledger and final reconciliation passed |
| `aql-recorder-j45jcx8` | Full `record` rerun | Succeeded; zero new filings, unchanged sequence 6/head |
| `aql-recorder-v0y8j22` | Read-only production evidence inspection | Succeeded; one filing, six audit events, DB/Blob reconciliation passed |

The two full successful runs reported zero **new** filings because the initial run
had already durably ingested the selected official filing. They are not claimed as
new downloads. The first full success added the September 14 checkpoint; the second
left the complete ledger unchanged. Final daily checkpoint dates are September 10,
11 and 14; no weekend checkpoint was manufactured.

Production head after both full runs:

```text
sequence = 6
hash = cff70005b296be1b43e85ccd67a094e27afdf82bf7d59706e2e131731d65e1cb
```

## Genuine missed-interval recovery

The [acceptance procedure](../infra/azure/scripts/live_sec_acceptance.py) used the
existing isolated `aql_test` database, which contained only the independently restored
universe baseline. It verified that baseline before writing and used a distinct
create-only Blob prefix, `acceptance/missed-sec-2026-09-10`.

It never called the latest feed. Official daily-index catch-up recovered accession
`0001140361-26-036226`, reconciled DB/ledger, restarted, then reran with zero new
filings and an exactly unchanged ledger. No production evidence or database was
cleared to simulate downtime.

Recovery observations:

```text
first_seen_at = 2026-09-14T19:20:43.822773+00:00
fetched_at = decision_eligible_at = 2026-09-14T19:20:44.028530+00:00
recovered_filings = 1
rerun_new_filings = 0
sequence = 4
hash = 21f0fac747b6d814d1894e35eabe928d3971283292cd041bb6f4f050375ee862
```

The recovered content hash equals production, while its observation times are later.
The one-time procedure refuses to overwrite an already used acceptance namespace
or adopt a database containing more than its expected baseline.

## Independent filing-bearing restoration

The actual six-record production Blob ledger was exported to ignored local
`infra/azure/.local/sec-official-export-20260915.jsonl`, with the expected sequence
and hash taken from job logs. Offline chain and evidence verification passed.

Both unchanged SQL migrations were applied to a **new** local PostgreSQL database,
`aql_restore_20260915`. With Azure and SEC access unnecessary, the exported local
ledger was replayed twice and reconciled. It contained six audit events, one
official filing and **zero duplicate `(source, external_id)` identities**, with
the exact original head. The disposable test database is not production storage;
the independent export and authoritative Azure Blob ledger are retained.

## Validation and monitoring boundaries

- Local tests: **232 passed, 3 skipped**, with real isolated PostgreSQL.
- The skips are the opt-in local live-SEC/live-Azure tests; no contact was extracted
  from the job to make those tests run. Real SEC acceptance was instead executed
  inside the configured Azure job, as documented above.
- Ruff check and formatting: passed, 45 Python files.
- Pyright: zero errors/warnings, including all operator helpers.
- Wheel/source build and runtime Bicep compilation: passed.
- ACR task `ca1b`: succeeded from commit `61ebc0790df93629fff4983eadb7a31cf86864b9`.
- [GitHub CI run 34928023575](https://github.com/BruceGK/agentic-quant-lab/actions/runs/34928023575):
  passed; 232 tests passed / 3 deselected, lint/types/package/image smoke checks passed.
- Actual Azure PostgreSQL append-only permissions and owner triggers were already
  exercised in the initial deployment: 27 real Azure tests and 12 production-role
  mutation denials. This update did not change those roles or migrations.
- Forty-three AQL console records checked after contact configuration contained
  **zero credential-pattern and zero email-pattern matches**. Only counts and
  explicitly whitelisted metadata were returned; the secret value was not inspected.
- Azure Monitor recognized the real `catch-up` completion and both full `record`
  completions at `2026-09-15T04:17:20Z` and `2026-09-15T04:18:53Z`, with the same
  verified sequence 6/head. It reported `SuccessfulIngestions=3`,
  `MissingSuccess=0`, and the previously demonstrated missing-success alert resolved.
  Earlier real failure and dead-man firing plus provider-confirmed Email Succeeded
  remain documented in the initial report. Human inbox receipt was not inspected.
- Direct operator PostgreSQL access timed out after the workstation public IP changed.
  No firewall or other infrastructure was changed to bypass it. Production inspection
  used the existing private job with its SEC secret removed from that inspection execution.

## Acceptance criteria

| Criterion | Result | Proof |
| --- | --- | --- |
| Real official SEC ingestion | PASS | Actual accession and content bytes durably recorded |
| Correct prospective timestamps | PASS | Actual production/recovery observations, never backdated |
| Idempotent filing rerun, zero duplicates | PASS | Official catch-up and full-record reruns; unchanged heads |
| Missed-interval recovery | PASS | One real filing recovered without latest-feed discovery; rerun zero |
| PostgreSQL append-only permissions | PASS | Previously exercised real Azure permissions/triggers; unchanged |
| Blob audit chain verifies | PASS | Independent verification of actual production and recovery chains |
| DB/ledger reconciliation | PASS | Real private job and restored database |
| Independent restoration/replay | PASS | Actual filing-bearing export, new database, two replays and reconcile |
| Manual Container Apps Job execution | PASS | Two full successful `record` executions |
| No observed secrets in Azure logs | PASS | Safe output and credential/email-pattern scans after live contact use |
| External monitoring path | PASS | Genuine reconciled ingestion recognized; notification path previously tested |
| Failure/missed-success alerts demonstrated | PASS | Actual firing previously demonstrated, healthy completion now recognized |

These results apply to the named deployment and executions, not to every future
installation or an arbitrary broader CIK universe.

## Scheduler and remaining operational actions

**Scheduling remains DISABLED.** The persisted Azure job is Manual; GitHub has no
recorder cron. The packaged policy flags were not changed by this task: recurring
activation and live execution remain blocked. This report records successful manual
external acceptance, not authorization to change the activation policy.

Optional GitHub OIDC activation still needs repository-admin environment protection
and variables; its Azure runner grant remains disabled. The earlier billing-meter
uncertainty and credit check remain operational follow-ups, not SEC acceptance failures.
No Phase 1, trading, broker or research-execution feature was introduced.

## Commits and image

- `66948cc` - preserve existing secret references through Bicep-resolved runtime PATCH;
  credential-safe diagnostics and isolated acceptance helpers.
- `61ebc07` - fail-closed handling for officially confirmed absent closed-day indexes.

Both commits were pushed without rewriting history. The deployed image is:

```text
riskpulseacr12345.azurecr.io/aql-recorder@sha256:ddac8132eb6a8f6cea09540e4a4cbf9c8701e3bf61b9a18b4818c7b629b55702
```
