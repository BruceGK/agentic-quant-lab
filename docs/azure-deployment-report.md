# Azure deployment and external acceptance - 2026-09-14

**Deployment is persistent; Phase 0 is NOT COMPLETE.**
The private Azure recorder can persist, reconcile and restore evidence, but no
official SEC filing was ingested because the real `SEC_USER_AGENT` is unavailable.
Successful maintenance commands are not substitutes for successful SEC recording.

Subscription: **Visual Studio Enterprise Subscription**,
`ccc5a11c-86d7-40f1-b02c-58660a2582a7`. Every Azure command explicitly targeted it.
The subscription is Enabled, its MSDN spending limit is On, and its existing
$150 billing-month budget was preserved. Neither a budget nor delayed cost data
establishes the exact remaining credit.

See [the reproducible operator runbook](../infra/azure/README.md).

## Existing infrastructure discovered

The original subscription contained:

- `RiskPulse/riskpulseacr12345`: Basic ACR, East US.
- `RiskPulse/managedEnvironment-RiskPulse-a04d`: Consumption environment, East US 2,
  no customer VNet.
- `RiskPulse/workspaceriskpulsebaaf`: Log Analytics, East US 2, 30-day retention.
- `RiskPulse/riskpulse-ca`: existing Container App.
- `RiskPulse/riskpulse-web`: existing static site.
- A default East US 2 Log Analytics workspace and a global RiskPulse
  Communication Services resource in `DefaultResourceGroup-EUS2`.

No PostgreSQL server, storage account, Container Apps Job, user-assigned identity
or Action Group existed. There was no suitable database to adopt.
East US, East US 2 and South Central US PostgreSQL provisioning were restricted;
Central US and West US 3 advertised eligible capacity.

## Git branches and history inspected

Fetched all remotes with pruning, inspected all advertised heads/reachable history,
historical paths and deployment-related content without switching the worktree.

| Source | Result |
| --- | --- |
| `copilot/phase-0-sec-filing-recorder` and its origin branch, initially `f841b00` | Integrity-first recorder, PostgreSQL migrations, filesystem ledger, CI, self-hosted recorder workflow |
| `origin/main`, `fb9b789` | Initial repository only; no reusable Azure deployment |
| Earlier reachable commits and checkpoint ref | No Azure/Bicep/Terraform/Docker/OIDC implementation |

Preserved all Phase 0 code and published history. No branch was force-pushed or merged
into the default branch. The old self-hosted cron was replaced by a manual-only
OIDC workflow; the packaged scheduled-recording and live-execution policies remain false.

## Reused

- Existing Basic ACR: added only the `aql-recorder` repository and AQL runtime AcrPull.
  Existing RiskPulse images, credentials, RBAC mode and application configuration
  were not changed.
- Existing Log Analytics workspace: new AQL environment diagnostics and AQL-specific
  alerts; existing workspace configuration and retention were not changed.
- Existing recorder integrity/replay/reconciliation logic and unchanged SQL
  migrations `001_evidence.sql` and `002_archive_recovery.sql`.
- The AQL PostgreSQL server, storage and runtime identity were preserved during
  the subsequent network correction.

The shared environment was genuinely tested first. Its outbound address changed
from `172.200.52.26` to `48.204.167.79` across executions, so a measured `/32` did not
make the next run reliable. Rather than allow all Azure IPs or modify RiskPulse,
the final job uses an AQL-only private network. The drained, data-free initial AQL
job was recreated in Central US. Only that AQL job was deleted; its failure history
was retained in this report/session evidence and its logs remain in Azure.

## Created

| Resource | Type | Region | SKU/configuration |
| --- | --- | --- | --- |
| `aql-phase0` | Resource group | East US 2 | AQL-only ownership tags |
| `aql-pg-6orzvtgi46z7e` | PostgreSQL Flexible Server | Central US | PostgreSQL 16, Burstable `Standard_B1ms`, 32 GiB P4, no HA, 7-day non-geo backups, autogrow off |
| `aql`, `aql_test` | PostgreSQL databases | Central US | Production projection and independent acceptance/restore database |
| `aql6orzvtgi46z7e` | StorageV2 account | East US 2 | Hot `Standard_LRS`, HTTPS/TLS 1.2, shared keys and anonymous Blob access disabled |
| `aql-audit-ledger`, `aql-audit-acceptance` | Blob containers | East US 2 | Separate production/test namespaces; versioning and 14-day blob/container soft delete; no WORM |
| `aql-recorder-runtime`, `aql-github` | User-assigned managed identities | East US 2 | Separate runtime and inactive GitHub automation principals |
| `aql-recorder-env` | Internal Container Apps environment | Central US | Workload-profiles environment containing only `Consumption` |
| `aql-recorder-vnet` | VNet/subnets | Central US | `10.86.0.0/24`, delegated jobs `/26`, separate endpoint `/28` |
| `aql-postgres-private` | PostgreSQL private endpoint | Central US | Approved `postgresqlServer` connection, private DNS resolves to `10.86.0.68` |
| `aql-postgres-private.nic.5fb8a235-87f5-4ea7-938d-59397c6e8ee5` | Managed endpoint NIC | Central US | No separate compute SKU |
| `privatelink.postgres.database.azure.com`, `aql-recorder-vnet` link | Private DNS zone/link | Global | Registration disabled |
| `aql-phase0-managed` / `capp-svc-lb` | Platform-managed group / load balancer | Central US | Internal Standard LB, two rules; no separately listed public-IP resource when inspected |
| `aql-recorder` | Container Apps Job | Central US | **Manual**, 0.5 CPU / 1 GiB, parallelism 1, completion count 1, retries 0, 1,800-second timeout |
| `aql-phase0-owners` | Action Group | Global | Subscription Owner role receiver; no committed email |
| `aql-recorder-failure`, `aql-recorder-missing-success` | Log alerts | East US 2 | Five-minute evaluation; 15-minute failure window; 24-hour missing-success threshold |
| `aql-phase0-costs` | Cost budget | Subscription | $65/month, filtered to both AQL groups; actual 80% and forecast 100% notifications |
| AQL scoped custom roles/assignments, GitHub federation, environment diagnostics | Access/configuration resources | Scoped/global | No subscription Owner grant; GitHub runner assignment disabled |

No NAT Gateway, AKS, VM, Redis, Cosmos DB, GPU, HA database, broker or Phase 1
infrastructure was created. Do not alter platform-managed LB/NIC children directly.

PostgreSQL is Entra-only. The operator has the separate migration/admin role.
`aql_recorder` has SELECT/INSERT on evidence, SELECT on views and no ownership,
schema creation, mutation, role inheritance or elevated server privileges.
`aql_research_reader` is SELECT-only and NOLOGIN. Public PostgreSQL firewall access
is limited to the operator's maintenance `/32`; runtime uses the private endpoint.

## Estimated monthly Azure cost

Approximate USD retail at 730 hours/month:

| New incremental component | Monthly estimate |
| --- | ---: |
| PostgreSQL compute | $14.02 |
| PostgreSQL 32 GiB storage | $3.68 |
| Managed Standard LB | $18.25 |
| PostgreSQL private endpoint | $7.30 |
| Private DNS zone | $0.50 |
| Two log alerts | $3.00 |
| Conservative outbound IPv4 allowance | $3.65 |
| **Planning subtotal** | **$50.40** |

Allow approximately **$50-55/month plus variable usage** under the documented
Consumption management-fee conditions. The initial $20-30 estimate became
inappropriate when actual tests disproved safe shared-environment reuse.
Blob operations/versions, job runs, log ingestion, cross-region traffic and
excess backup usage remain metered. Existing/shared Basic ACR is roughly $5/month
already incurred; other RiskPulse compute/log costs were not re-estimated or removed.

**Cost uncertainty:** the retail catalog also lists an insufficiently documented
`Environment Management Hour` meter at $0.10/hour. Applicability to this
Consumption-only configuration could not be independently established; if charged,
it adds about $73/month. No dedicated profile, ACA inbound private endpoint or
paid planned-maintenance feature was enabled. The runbook links official billing
conditions. Verify the actual bill; do not treat this estimate as a guarantee.
Both budgets reported $0 current spend when queried, which can reflect metering delay.
Budget alerts are not spending caps; the subscription's separate spending-limit policy is On.

## Validation

| Check | Exact result |
| --- | --- |
| `TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55432/quant_test uv run --frozen pytest -q` | **206 passed, 3 skipped**: two live SEC tests and one explicitly opt-in Azure test |
| `uv run --frozen ruff check .` | Passed |
| `uv run --frozen ruff format --check .` | Passed; 41 Python files |
| `uv run --frozen pyright` | Zero errors/warnings; default scope includes all new deployment scripts/tests |
| `uv build --no-sources` | Wheel and source distribution built |
| Bicep build for foundation, network, runtime and cost entrypoints | All passed without warnings; real what-if/apply also exercised |
| `bash -n infra/azure/deploy.sh`; `git diff --check` | Passed |
| Pinned non-root production image build/smoke tests | Passed: UID 10001, TLS trust, runtime imports, no pytest/uv in runtime, safe nonzero failure |
| Real ACR build task `ca1a` | Succeeded from immutable commit `d21960c` |
| Real Azure targeted pytest | **27 passed**: live Blob export/replay to Azure PostgreSQL, 24 writer/owner mutation cases, idempotent replay, ledger-before-DB recovery |
| Actual production writer permission probes | All 12 UPDATE/DELETE/TRUNCATE attempts rejected with insufficient privilege; rollback-protected |
| Production bootstrap check and idempotent reapply | Passed; authoritative migration checksums and schema hash unchanged |
| Secret-pattern scan of 14 AQL console records | Zero credential patterns; no live SEC contact was present |
| Read-only runtime and infrastructure security specialist checks | No high-confidence exploitable vulnerabilities found |
| CodeQL | Not run: no CLI available; GitHub setup/analysis APIs returned HTTP 403 |

The real Azure pytest command selected:

```text
tests/test_live_azure.py
tests/test_recorder.py::test_database_append_only
tests/test_recorder.py::test_projection_replay_is_idempotent
tests/test_recorder.py::test_crash_after_fsync_replays_projection
```

It used a short-lived Entra token in process memory/environment, the isolated
`aql_test` database and `aql-audit-acceptance` container. Synthetic SEC fixture data
was confined to disposable test schemas, not production SEC evidence.

**Real GitHub CI passed** on published code commit `5a86f88`:
[run 34817698134](https://github.com/BruceGK/agentic-quant-lab/actions/runs/34817698134).
Its logs confirm 206 passed / 3 deselected, clean lint/types, package build and the
secret-free production-image build/smoke steps.

## Real external paths exercised

- Private job `aql-recorder-x1z0515` verified private DNS `10.86.0.68`, outbound
  HTTPS, actual managed-identity login as `aql_recorder` to `aql`, and Blob access.
- `aql-recorder-cg8b8qc` durably recorded the real configured universe snapshot.
  `aql-recorder-ayaoeiq` reran it without another event.
- `aql-recorder-705fbsz` and `aql-recorder-y7h54hg` reconciled PostgreSQL with Blob.
  The latter succeeded after obsolete public runtime firewall access was removed.
- The actual nonempty Blob chain was independently exported to JSONL and verified
  against its logged head, replayed twice into Azure `aql_test`, then reconciled.
  Both databases contain exactly one universe event and zero SEC filings.
- `aql-recorder-r5djbt2` actually started the container and failed `record` safely
  with `{"status":"failed","error":"recorder_failed"}` while contact was absent.
  It emitted no ingestion-completed event.
- Real classic and resource-specific logs reached the reused workspace. No
  maintenance success counted as a completed ingestion heartbeat.
- Failure alert `7dcf663e-5fa9-b19a-4cd3-adf0e9840004` fired at
  `2026-09-14T05:52:54Z`. Missing-success alert
  `c306bd32-3916-f4db-0b62-5e321ec30004` fired at `2026-09-14T06:14:41Z`.
  Private-job recording failure subsequently fired
  `6500e74c-eca4-e372-9ce4-07c7f22a0004`.
- The Owner Action Group's actual notification test reported **Email Succeeded**.
  Human inbox receipt was not independently inspected. The temporary five-minute
  dead-man override was restored; the final threshold is 1,440 minutes.

Verified sequence/head:

```text
sequence = 1
prev_hash = 0000000000000000000000000000000000000000000000000000000000000000
record_hash = 471d655490eb45dcdba5ee2a24b3dfbfafd32abb989ebcb9b035ba22233841ea
```

Published runtime image:

```text
riskpulseacr12345.azurecr.io/aql-recorder@sha256:85a660fee802a329cb68b552e4bbf7eb50da70946cf7a4621141daf8012377a9
```

## Remaining blockers

1. **SEC acceptance:** privately set the genuine `SEC_USER_AGENT` through the
   [runbook's runtime secret procedure](../infra/azure/README.md#build-pin-and-deploy).
   It writes the `sec-user-agent` secret on `aql-phase0/aql-recorder`.
   Do not put the contact in Git, the image or CI. This is the single missing
   SEC user action; an authorized follow-up can then perform the real filing,
   timestamp, duplicate and daily-index recovery checks.
2. **Optional GitHub automation:** an authorized repository administrator must
   configure the protected `azure-production` environment, restrict it to the
   reviewed default branch, set the documented nonsecret OIDC variables and then
   enable the narrow runner assignment. Current token attempts returned 403.
   Federation exists, but the GitHub identity was verified to have **zero Azure
   role assignments**. Manual Azure operation does not depend on this.
3. **Billing verification:** inspect actual AQL and managed-network charges when
   metering is available, especially the ambiguous management meter. The $65
   budget and subscription spending limit are guardrails, not a price guarantee.
4. **Optional CodeQL:** run analysis from an authorized security-analysis context;
   this session has no CodeQL CLI and its GitHub code-scanning API access returns 403.
   This does not invalidate the separately successful CI and manual security reviews.

## Phase 0 acceptance

FAIL below includes unexercised/blocked paths, not merely failed assertions.

| Criterion | Result | Evidence boundary |
| --- | --- | --- |
| Real official SEC ingestion | **FAIL** | No contact; no official filing ingested |
| Correct prospective filing timestamps | **FAIL** | No official filing exists to inspect; synthetic checks are not a substitute |
| Idempotent official-filing rerun, zero duplicates | **FAIL** | Universe rerun passed; official filing rerun unexercised |
| Missed-interval recovery | **FAIL** | Regression coverage passes; real daily-index catch-up unexercised |
| PostgreSQL append-only permissions | **PASS** | Actual writer denials and real Azure owner-trigger tests |
| Blob audit chain verifies | **PASS** | Real nonempty universe chain and independent expected head |
| DB/ledger reconciliation | **PASS** | Real private job and independent restored database |
| Independent restoration/replay | **PASS** | Export, offline verification, two replays and reconciliation |
| Manual recorder ingestion execution | **FAIL** | Maintenance executions passed; full `record` remains contact-blocked |
| Azure logs contain no observed secrets | **PASS** | Real MI-backed runs, fixed error output and bounded log scan |
| External monitoring path | **PASS** | Live log routing and provider-confirmed Email Succeeded; inbox not inspected |
| Failure/missed-success alert demonstration | **PASS** | Real Fired alerts; no fabricated ingestion heartbeat |

## Scheduler

**DISABLED.** The Azure trigger is Manual; the GitHub workflow has no cron.

```text
scheduled_recording_enabled = false
live_execution_enabled = false
external_acceptance_complete = false
```

Failure/dead-man monitoring stays enabled. Phase 0 must not be declared complete
or recurring recording enabled until the blocked real SEC gates pass.

## Commits

Published non-destructively on `copilot/phase-0-sec-filing-recorder`:

- `de42d0c` - durable Blob ledger, independent export, Entra auth and success semantics.
- `d21960c` - pinned, minimal non-root recorder image.
- `2d1fb7b` - reproducible Azure/private-network deployment, roles, alerts and guarded tools.
- `5a86f88` - real Azure acceptance test, isolated CI image validation and documentation.

This report is a documentation-only follow-up to the verified code commits.

## Next action

**Privately configure the real `SEC_USER_AGENT` on the Azure job using the runbook,
then resume official SEC acceptance. Keep scheduling disabled.**
