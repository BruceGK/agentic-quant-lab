# Azure Phase-0 recorder: manual acceptance only

This is an **operator-run foundation/network/runtime deployment**, not evidence that SEC access,
OIDC, or alert delivery has passed acceptance. No schedule is declared anywhere in this
surface. The packaged constitution remains authoritative: scheduled recording and live
execution stay disabled, and external acceptance remains incomplete. This does not
implement Phase 1, a live research service, or trading.

All scripts pin subscription `ccc5a11c-86d7-40f1-b02c-58660a2582a7`, check it before
each CLI operation, and pass `--subscription` explicitly. They never change the default
subscription. Their entrypoints also set process-local `AZURE_SUBSCRIPTION_ID` after
rejecting conflicting overrides; the job carries the same nonsecret environment variable.
Run them from this repository. `deploy.sh` defaults to **ARM what-if**;
bootstrap/job/alert demonstrations require `--apply`. Scripts suppress raw provider
errors because those can repeat secret parameters. Review failed deployment operation
**error codes**, not unredacted secret-bearing request/response bodies.

```bash
az deployment operation sub list --subscription ccc5a11c-86d7-40f1-b02c-58660a2582a7 \
  --name aql-phase0-foundation --output json \
  --query "[?properties.provisioningState=='Failed'].{target:properties.targetResource.id,code:properties.statusMessage.error.code}"
az deployment operation group list --subscription ccc5a11c-86d7-40f1-b02c-58660a2582a7 \
  --resource-group aql-phase0 --name aql-phase0-runtime --output json \
  --query "[?properties.provisioningState=='Failed'].{target:properties.targetResource.id,code:properties.statusMessage.error.code}"
```

## Resource and permission boundaries

| Existing/shared, referenced with `existing` only | New AQL resources |
| --- | --- |
| `RiskPulse/riskpulseacr12345`, Basic, eastus | `aql-phase0` resource group, eastus2 |
| RiskPulse's no-VNet environment was tested, then left unchanged | `aql-recorder` **Manual** Container Apps Job, centralus |
| `RiskPulse/workspaceriskpulsebaaf`, eastus2, existing 30-day retention | `aql-recorder-runtime` and `aql-github` user-assigned identities |
| Other RiskPulse applications/resources are outside this deployment | Deterministic `aql<13-character suffix>` StorageV2 / Standard_LRS account |
| Workspace customer ID `c75d8583-dbe6-4e57-9cd5-70097059f1ce` | `aql-pg-<same suffix>` PostgreSQL 16 Flexible Server, **centralus** |
| No workspace/registry/environment settings are changed | AQL-only Owner Action Group, two 5-minute log alerts, narrowly scoped roles |
| Existing PostgreSQL is retained during the network cutover | Internal Consumption environment, VNet, PostgreSQL private endpoint and private DNS |

The shared environment's actual egress changed between executions. Approving one
observed `/32` did not make the next execution reliable. The final deployment
therefore uses `aql-recorder-env` in CentralUS, not that shared environment.
It reuses the same ACR, Log Analytics workspace, PostgreSQL server, storage and UAMI.
There is no NAT Gateway, dedicated workload profile, inbound ACA private endpoint,
VM or AKS deployment. Platform networking is in `aql-phase0-managed`; never edit
or delete those platform-managed children directly.

The suffix is `uniqueString(subscription().subscriptionId, resourceGroup().id, 'aql-phase0')`.
The foundation writes one narrowly scoped **AcrPull role assignment** in RiskPulse;
it does not redeploy that registry or any shared application/environment/workspace.
There are no subscription-scope role assignments.

* PostgreSQL: `Standard_B1ms`, Burstable, 32 GiB, 7-day non-geo backups, no HA,
  storage autogrow disabled. Entra authentication is enabled; password authentication
  is disabled. Runtime connects over a private endpoint in `aql-recorder-vnet`.
  Only the operator's explicit public IPv4s are allowed for maintenance; each becomes one
  start-IP=end-IP `/32` rule. Never use `0.0.0.0`, a global range, or
  “allow all Azure services.” CentralUS was subscription-eligible during discovery;
  eastus/eastus2/southcentralus were blocked. WestUS3 is an explicit fallback parameter,
  not an automatic region change.
* Blob: private `aql-audit-ledger` container; HTTPS, TLS 1.2, shared keys disabled,
  blob versioning and **14-day blob and container soft delete**. Its endpoint remains
  public HTTPS and authorized with Entra, not anonymously accessible. The private
  endpoint is for PostgreSQL, not Blob; no WORM policy is claimed.
* Runtime: container-scoped custom Blob read/write role **without delete**, ACR-scoped
  AcrPull, and PostgreSQL role `aql_recorder` mapped by the UAMI's **principal/object ID**,
  not its client ID. It can SELECT+INSERT the four evidence tables and SELECT the two
  views. No ownership, role memberships, grant options, schema creation, temporary
  tables, UPDATE, DELETE, TRUNCATE, DDL, CREATEDB, or CREATEROLE in the evidence database.
  The unmapped `aql_research_reader` role is SELECT-only and **NOLOGIN**. The migration
  administrator is separate.
* GitHub: separate identity, exact federated subject
  `repo:BruceGK/agentic-quant-lab:environment:azure-production`; job-scoped custom
  read/start/execution-read role only, initially **not assigned**
  (`githubRunnerEnabled=false`). No job write, list-secrets, Blob/SQL data access,
  ACR access, role assignments, or ARM deployment permission. It is **run-only**.
  Container Apps' start API permits execution template overrides, so starting a job
  is a trusted code-execution capability with its runtime identity. Environment and
  default-branch protection are essential; read/start is not a sandbox.

Blob `write` permission also permits overwriting an existing blob. Atomic create-only
`If-None-Match: *`, canonical hash chaining, remote verification, and the PostgreSQL
advisory writer lock enforce the application protocol; they are **not storage WORM**.
Versioning/soft delete help recovery but do not protect against a malicious subscription
Owner. Independently retain verified sequence/head checkpoints. The layout is
`sec/records/{sequence:020d}.jsonl`; no blob lease permission is needed.

## Cost gate

Incremental planning estimate, **not a bill, credit balance, or guarantee**:

| Increment | Approximate monthly USD |
| --- | ---: |
| CentralUS B1ms compute, observed public rate $0.01921/hour × 730 | $14.02 |
| 32 GiB PostgreSQL storage at approximately $0.115/GiB | $3.68 |
| Two 5-minute non-dimensional query alerts | Allow approximately $3; verify current pricing |
| Managed Standard Load Balancer, first five rules | $18.25 |
| PostgreSQL private endpoint | $7.30 |
| Private DNS zone | $0.50 |
| Conservative allowance for an outbound public IPv4 meter | $3.65 |
| Small manual jobs, Blob requests/versions, new log ingestion, inter-region transfer | Usage-dependent |

Plan approximately **$50–55/month incremental** at acceptance volume, not the original
$20–30 estimate that assumed the shared environment was usable. The managed RG
currently exposes one internal Standard LB with two rules and no public-IP resource;
the public-IP line is a conservative allowance, not a claim that one was observed.
The existing ACR, workspace, environment, RiskPulse workloads and their costs are not
free and are not recreated. Consumption free grants are subscription-wide. PostgreSQL
and the new job are colocated; ACR/Blob/log traffic crosses regions.
Version retention and failed jobs still consume
resources. The existing $150 budget is not proof of remaining sponsorship credit.
PostgreSQL and private networking incur cost even with scheduling disabled.

The [documented management-fee conditions](https://learn.microsoft.com/azure/container-apps/billing)
do not include a Consumption-only profile merely accessing a PostgreSQL private endpoint.
However, the current retail catalog lists an insufficiently documented
`Environment Management Hour` meter at $0.10/hour. If applicable, it adds about
$73/month. **Actual applicability and remaining credit are not verified.**
Check Cost Management billing rather than treating an estimate as a guarantee.
`cost.bicep` provisions a separate $65 AQL budget covering both AQL resource groups,
with actual-80% and forecast-100% notifications to the tested Owner Action Group.
The existing subscription budget is unchanged. Budgets notify; they are **not spending caps**.

For the optional cost deployment, copy `cost.parameters.example.json` into `.local/`,
set `startDate` to the first day of its creation month (for example
`2026-09-01T00:00:00Z`), and retain that date on subsequent deployments:

```bash
az deployment sub what-if --subscription ccc5a11c-86d7-40f1-b02c-58660a2582a7 \
  --location eastus2 --name aql-phase0-costs --template-file infra/azure/cost.bicep \
  --parameters @infra/azure/.local/cost.parameters.json
az deployment sub create --subscription ccc5a11c-86d7-40f1-b02c-58660a2582a7 \
  --location eastus2 --name aql-phase0-costs --template-file infra/azure/cost.bicep \
  --parameters @infra/azure/.local/cost.parameters.json
```

## 1. Prepare nonsecret parameters

Prerequisites: operator Owner (already verified during discovery), logged-in Azure CLI,
Bicep, Python 3.12, and the repository's existing `uv` environment with psycopg. No
service-principal password, database password, new email, or directory-wide Graph role
is required. Do not print access tokens.

```bash
az account show --subscription ccc5a11c-86d7-40f1-b02c-58660a2582a7 \
  --query '{id:id,tenantId:tenantId}' --output json
az bicep version --subscription ccc5a11c-86d7-40f1-b02c-58660a2582a7
# Only if the preceding command reports Bicep missing:
# az bicep install --subscription ccc5a11c-86d7-40f1-b02c-58660a2582a7

umask 077
mkdir -p infra/azure/.local
cp infra/azure/foundation.parameters.example.json infra/azure/.local/foundation.parameters.json
cp infra/azure/network.parameters.example.json infra/azure/.local/network.parameters.json
cp infra/azure/runtime.parameters.example.json infra/azure/.local/runtime.parameters.json

ADMIN_OBJECT_ID="$(az rest --subscription ccc5a11c-86d7-40f1-b02c-58660a2582a7 \
  --method get --url 'https://graph.microsoft.com/v1.0/me?$select=id' --query id --output tsv)"
export ADMIN_OBJECT_ID
# Fill operatorIpv4Addresses; keep environmentOutboundIpv4Addresses empty for private networking.
# Also replace administratorObjectId with ADMIN_OBJECT_ID in foundation.parameters.json.
```

Parameter files contain only literals, never contacts, tokens, or password material.
The example placeholders intentionally fail validation. Supply the operator's
approved public IPv4, without a CIDR suffix. The runtime uses private DNS and the
PostgreSQL private endpoint, so keep `environmentOutboundIpv4Addresses` empty.

Discovery reported environment `staticIp=135.237.206.62` and
`outboundIpAddresses=null`. **The static IP is not proof of outbound egress.** The
existing app exposes hundreds of possible outbound IPs; do not blindly allowlist that
list. Both `172.200.52.26` and `48.204.167.79` were observed in different executions;
this ruled out a stable observed-IP solution. No such discovery IP is required by
the final runtime. `probe-connections` now requires private PostgreSQL DNS resolution.

`administratorPrincipalName` is `aql_migration_admin`, mapped to the supplied current
CLI user's object ID. This safe alias is exposed by the ARM administrator schema, but
its acceptance was verified on the real server. If another deployment rejects it,
stop and review the Entra administrator
mapping; do not silently enable password authentication or substitute the runtime user.
The SQL `pgaadauth_create_principal_with_oid` interface explicitly allows the runtime's
arbitrary role name `aql_recorder`, independent of the UAMI display name.

Set `createTestDatabase: true` only if the isolated `aql_test` database is wanted.
This also creates `aql-audit-acceptance`, with operator Blob Data Contributor
access limited to that test container. The operator has Blob Data Reader on
`aql-audit-ledger` for independent export; only the runtime has production
write permission. No test cleanup deletes production ledger records.
Default missing-ingestion threshold is 1440 minutes, adjustable from 5 to 1440. The
dead-man alert is expected to fire when manual acceptance is dormant.

## 2. Foundation, then authoritative SQL

```bash
bash infra/azure/deploy.sh foundation \
  --parameters infra/azure/.local/foundation.parameters.json
# Review resource IDs; only AQL resources and AQL's shared-registry role may be writes.
bash infra/azure/deploy.sh foundation \
  --parameters infra/azure/.local/foundation.parameters.json --apply

# Local bootstrap plan; does not connect to Azure/PostgreSQL:
uv run --frozen python infra/azure/scripts/bootstrap.py
uv run --frozen python infra/azure/scripts/bootstrap.py --apply
uv run --frozen python infra/azure/scripts/bootstrap.py --check
# Only if createTestDatabase was true:
uv run --frozen python infra/azure/scripts/bootstrap.py --database aql_test --apply
```

Foundation output is `infra/azure/.local/foundation.outputs.json`, an ARM outputs
object (`.name.value`). Important stable keys:

* `subscriptionId`, `tenantId`, `resourceGroupName`, `postgresLocation`
* `postgresServerName`, `postgresServerId`, `postgresHost`, `databaseName`, `testDatabaseName`
* `administratorObjectId`, `administratorPrincipalName`, **nonsecret** `databaseUrl`
* `storageAccountName`, `storageAccountId`, `storageAccountUrl`, `storageContainerName`, `ledgerPrefix`
* `runtimeIdentityId`, `runtimeClientId`, `runtimePrincipalId`
* `githubIdentityId`, `githubClientId`, `githubPrincipalId`, `githubFederatedSubject`
* `registryId`, `registryLoginServer`, `jobName`
* `actionGroupId`, `failureAlertId`, `missingSuccessAlertId`, `workspaceId`,
  `workspaceCustomerId`, `staleAfterMinutes`

Outputs and receipts are mode 0600 in ignored `.local/`; no token/contact is output.
The scripts use the default subscription deployment name `aql-phase0-foundation` and
group deployment name `aql-phase0-runtime`. Deployments are incremental. Because ARM
incremental mode retains omitted firewall children, the foundation script additionally
lists and removes **only its own obsolete `aql-<IPv4>` /32 rules on the new AQL server**
on apply; what-if lists these planned removals separately. Unexpected rules or multiple
AQL servers fail closed. Removing an optional database from parameters does **not**
delete it. There is deliberately no teardown or complete-mode deployment script.

Bootstrap fetches the current operator token into process memory, checks the Graph
object ID, tenant, server endpoint/version/authentication, and UAMI mapping, then uses
libpq **`sslmode=verify-full sslrootcert=/etc/ssl/certs/ca-certificates.crt`**. Principal
management uses only the new server's built-in `postgres` database. Evidence/schema
operations target only the explicitly selected `aql` or `aql_test`, never a pre-existing
RiskPulse database.

The only authoritative evidence migrations are the repository's unchanged
`migrations/001_evidence.sql` and `002_archive_recovery.sql`. Bootstrap executes their
bodies unchanged, replacing only their outer BEGIN/COMMIT wrappers so migration plus
SHA-256 receipt commit atomically. Receipts live in protected
`aql_admin.schema_migrations`, not in evidence tables. It refuses:

* untracked pre-existing tables/views/functions or metadata;
* unknown, missing/out-of-order, or changed migration checksums;
* changed schema definitions, owners, constraints, views, functions, or trigger enablement;
* runtime Entra remapping, elevated attributes, ownership, or role memberships.

Firewall updates finish before Entra administrator operations; running those provider
operations concurrently can transiently make PostgreSQL inaccessible. Re-running
is idempotent and checks the actual grants. It takes the recorder's advisory
writer lock before migration; do not start jobs during bootstrap. It does not drop data
or bypass append-only triggers. `bootstrap-aql.json` / `bootstrap-aql_test.json` record
only hashes, target identity, and checked privilege status.
Both `--apply` and `--check` additionally execute twelve UPDATE/DELETE/TRUNCATE
permission probes under `SET LOCAL ROLE aql_recorder`. Every probe is rollback-protected,
must fail with insufficient privilege, and cannot quietly pass because a trigger alone
blocked an overprivileged writer.

## 3. Private network, then the manual runtime

```bash
bash infra/azure/deploy.sh network \
  --parameters infra/azure/.local/network.parameters.json
bash infra/azure/deploy.sh network \
  --parameters infra/azure/.local/network.parameters.json --apply
```

The network phase derives the server and region from foundation outputs. It creates
`aql-recorder-vnet` (`10.86.0.0/24`), a delegated jobs `/26`, a separate endpoint `/28`,
`aql-postgres-private`, and `privatelink.postgres.database.azure.com` with its VNet link.
The internal environment contains only the `Consumption` profile. Managed egress
provides public SEC/ACR/Blob/Entra connectivity; database access does not depend on that
public egress address. Continue using the original PostgreSQL FQDN and `verify-full`
TLS, not the private IP, in the DSN.

The environment routes resource-specific console/system logs through diagnostic settings
to the existing workspace without workspace keys. `network.outputs.json` retains
its environment, VNet, endpoint, DNS and managed-resource-group IDs.

An EastUS2 job cannot be moved across regions in place. The initial AQL acceptance job
was drained, its execution history recorded, and **only that AQL job** deleted/recreated
in CentralUS. PostgreSQL, Blob and the UAMI were preserved; RiskPulse was not changed.
Fresh deployments do not need this migration. Never delete an active job or a shared
environment to work around a region mismatch.

### Build, pin and deploy

Build is an **operator action**, not a capability of `aql-github`. Build only the reviewed
clean commit, use the repository Dockerfile, and never send contact/token/DSN secrets as
build args or environment values. The Docker context allowlist excludes `infra/` and
`.local/`. An explicit operator ACR build example:

```bash
test -z "$(git status --porcelain)"
GIT_SHA="$(git rev-parse HEAD)"
az acr build --subscription ccc5a11c-86d7-40f1-b02c-58660a2582a7 \
  --registry riskpulseacr12345 --image "aql-recorder:git-$GIT_SHA" --file Dockerfile .
DIGEST="$(az acr repository show --subscription ccc5a11c-86d7-40f1-b02c-58660a2582a7 \
  --name riskpulseacr12345 --image "aql-recorder:git-$GIT_SHA" --query digest --output tsv)"
# Set imageRef to riskpulseacr12345.azurecr.io/aql-recorder@$DIGEST in the runtime file.
# Set recorderGitSha to GIT_SHA and catchupStart to an explicitly reviewed YYYY-MM-DD.
```

Prefer the digest. A `git-<40hex>` tag is accepted only if its SHA matches
`recorderGitSha` and ACR reports both `writeEnabled=false` and `deleteEnabled=false`.
These scripts never lock/unlock shared registry repositories or change ACR RBAC mode.
The discovered ACR `roleAssignmentMode` is `LegacyRegistryPermissions` and is not
changed. Legacy ACR `AcrPush` is registry-wide, not restricted to an AQL repository; a future
GitHub build/deploy workflow would need a separately reviewed permission design.

```bash
bash infra/azure/deploy.sh runtime \
  --parameters infra/azure/.local/runtime.parameters.json
bash infra/azure/deploy.sh runtime \
  --parameters infra/azure/.local/runtime.parameters.json --apply
```

An absent SEC contact is supported for infrastructure/monitor acceptance. It is **not**
silently replaced with a fake identity: recording must visibly fail until a genuine
contact is configured. The initial job is `.5 CPU / 1 GiB`, completion count 1,
parallelism 1, retry limit 0, timeout 1800 seconds (optionally 3600), command entrypoint
`quant-recorder`, arguments `record`, `RECORDER_RUN_MODE=acceptance`. There is no
`Schedule` trigger. Both CIK settings default to `320193` only as the acceptance
universe; review before any later scope expansion.

Configure/update the contact out of band; it becomes a job secret named `sec-user-agent`:

If this secret already exists, set `useExistingSecUserAgentSecret` to `true` in
the runtime parameters, then run the runtime what-if/apply commands above.
This mode reads only ordinary job metadata and emits `SEC_USER_AGENT` with
`secretRef: sec-user-agent`. Bicep resolves the desired nonsecret configuration and
template, and the helper applies them using the job PATCH API, omitting the secret
collection. It deliberately skips a full job PUT because Azure what-if shows that
PUT could delete externally configured secrets. Use the helper, not a direct ARM
deployment, to apply reference-only updates. It does not call `listSecrets`, read
the contact from the local environment, or require supplying the identity again.
The job must already contain the secret.

Only for initial provisioning or an explicitly requested secret-value update,
leave the flag false and supply the contact privately:

```bash
set +x
read -r -s -p 'Genuine SEC user-agent/contact: ' SEC_USER_AGENT
printf '\n'
export SEC_USER_AGENT
bash infra/azure/deploy.sh runtime \
  --parameters infra/azure/.local/runtime.parameters.json
bash infra/azure/deploy.sh runtime \
  --parameters infra/azure/.local/runtime.parameters.json --apply
unset SEC_USER_AGENT
```

The deploy helper creates a mode-0600 parameter file under ignored `.local/`, passes only
its filename to Azure CLI, suppresses provider output, and removes the file in `finally`.
Do not terminate it with SIGKILL or enable shell/CLI debug logging. On subsequent
deployments, use reference-only mode rather than supplying the contact again.
The script refuses to implicitly unmap an already configured secret.
Never commit it or put it in GitHub variables/build args.
No database password or heartbeat webhook is needed. Alerting uses stdout completion
events and the existing workspace, not a secret-bearing HTTP hook.

Runtime outputs are in `infra/azure/.local/runtime.outputs.json`: `jobId`, `jobName`,
`environmentId`, `imageRef`, `recorderGitSha`, `databaseUrl`, `storageAccountUrl`,
`runtimeClientId`, `githubClientId`, and the pinned subscription/group identifiers.

## 4. Manual operation, remote verification, export/replay

```bash
python3 infra/azure/scripts/job.py --command verify-blob --apply
python3 infra/azure/scripts/job.py --command snapshot --apply
python3 infra/azure/scripts/job.py --command reconcile --apply
python3 infra/azure/scripts/job.py --command record --apply
# Read-only metadata inspection: the execution does not receive SEC_USER_AGENT.
python3 infra/azure/scripts/job.py --command inspect-evidence --apply
# Explicit one-off catch-up, not a recurring trigger:
python3 infra/azure/scripts/job.py --command catch-up \
  --start "$REVIEWED_START" --end "$REVIEWED_END" --apply
```

Without `--apply` these commands only print a local plan. They do not update the stored
job definition. They reject active/unknown executions and wait for terminal status by
default (`--no-wait` only submits). GitHub concurrency and job parallelism do not lock
two independent executions against one another; the existing database advisory lock is
the final single-writer guard.

Optional `--receipt infra/azure/.local/execution.json` retains only the execution ID
and status, including on failure. `probe-sec` and `probe-sec-directory` perform bounded
diagnostic requests inside the job, returning only parser counts, public index metadata
and HTTP status codes, never contact values, headers or response bodies.
`accept-missed-interval` is a **one-time** isolated acceptance operation: `aql_test`
must contain only the verified initial universe baseline, and its distinct
`acceptance/missed-sec-<date>` Blob prefix must be unused. It recovers a real
filing without calling the latest feed, then repeats catch-up to assert zero duplicates.
Do not clear an existing projection or prefix to rerun this acceptance helper.

**`Succeeded` is not ingestion proof.** Only `aql.recorder.completed` with
`status=success`, `ledger_backend=azure`, `reconciliation=passed`, and command
`record`/`catch-up` qualifies. The CLI emits it only after real ingestion, remote chain
verification, and database reconciliation. Snapshot/replay/reconcile/help, container
startup, and an empty job result never satisfy the dead-man alert.

For independent export, foundation grants the configured operator container-scoped
Blob Data Reader on the production ledger. Owner alone is not a data role. When
`createTestDatabase=true`, the operator has Blob Data Contributor on the separate
`aql-audit-acceptance` container. GitHub has neither grant. Do not broaden the runtime's
no-delete role or use production records for destructive acceptance tests.

```bash
export AZURE_SUBSCRIPTION_ID=ccc5a11c-86d7-40f1-b02c-58660a2582a7
export LEDGER_BACKEND=azure
export AZURE_STORAGE_ACCOUNT_URL="$(jq -r '.storageAccountUrl.value' infra/azure/.local/foundation.outputs.json)"
export AZURE_STORAGE_CONTAINER=aql-audit-ledger
export AZURE_LEDGER_PREFIX=sec
# EXPECTED_HEAD and EXPECTED_SEQUENCE must come from an independently retained checkpoint.
uv run --frozen quant-recorder verify-blob \
  --expected-head "$EXPECTED_HEAD" --expected-sequence "$EXPECTED_SEQUENCE"
uv run --frozen quant-recorder export-ledger infra/azure/.local/ledger-export.jsonl \
  --expected-head "$EXPECTED_HEAD" --expected-sequence "$EXPECTED_SEQUENCE"
uv run --frozen quant-recorder verify infra/azure/.local/ledger-export.jsonl \
  --expected-head "$EXPECTED_HEAD" --expected-sequence "$EXPECTED_SEQUENCE"
```

Replay missing projections inside the runtime with
`python3 infra/azure/scripts/job.py --command replay --apply`, followed by reconcile.
Replay is not permission to clear, rebuild, or overwrite a live evidence database.
For an **independent, empty isolated test database**, bootstrap `aql_test` as above,
then use the operator's migration role and exported local ledger:

```bash
PGHOST="$(jq -r '.postgresHost.value' infra/azure/.local/foundation.outputs.json)"
export DATABASE_AUTH=azure
export DATABASE_URL="host=$PGHOST port=5432 dbname=aql_test user=aql_migration_admin sslmode=verify-full sslrootcert=/etc/ssl/certs/ca-certificates.crt"
export LEDGER_BACKEND=local
export LEDGER_PATH="$PWD/infra/azure/.local/ledger-export.jsonl"
export UNIVERSE_CIKS=320193
uv run --frozen quant-recorder replay
uv run --frozen quant-recorder reconcile
```

With `IDENTITY_ENDPOINT` present, the recorder uses
`ManagedIdentityCredential(client_id=AZURE_CLIENT_ID)`. Otherwise it uses
`AzureCliCredential(subscription=AZURE_SUBSCRIPTION_ID)`: the subscription-pinned current
CLI user, not an impersonation of the UAMI. The `export AZURE_SUBSCRIPTION_ID=...` above
is required for standalone local `quant-recorder` invocations; an operator helper's
process environment cannot change its parent shell. Never try to authenticate the
current operator token as `aql_recorder`.
Do not run root integration tests against `aql` or overwrite live evidence to prove
recovery. An aql_test replay is not an ingestion-success heartbeat.

## 5. AQL monitoring and delivery acceptance

Foundation provisions `aql-phase0-owners`, `aql-recorder-failure`, and
`aql-recorder-missing-success` even before a runtime image/contact exists. Receiver is
the built-in **Subscription Owner** ARM role (`8e3af657-a8ff-443c-a75c-2fe8c4bcb635`),
not a new or committed email. Role notification eligibility matters: eligible-only PIM,
service principals, and indirect group membership must not be assumed to receive email.
An enabled receiver is not evidence of real delivery.

Queries live in `queries/`, share job-specific filters, tolerate the documented console/
system table and job-name column variants, and include a typed empty input. Ungrouped
`summarize count()` makes **no rows / never succeeded** alertable. Rules measure explicit
numeric `Failures` and `MissingSuccess` columns using Maximum > 0, not a fabricated
current-time log row. The 2-day query bound
covers every supported stale threshold; failure uses a 15-minute lookback. Both rules
evaluate every 5 minutes, are stateful (`autoMitigate=true`), and notify the AQL Action
Group. Missing ingestion is expected while acceptance remains manual.

`skipQueryValidation=false` requires Azure query validation. Actual classic and
resource-specific log schemas were exercised; a local build alone is not proof.
Foundation registers the required Alerts Management and Resource Health providers.
Status inspection handles pagination and case-insensitive ARM resource IDs rather than
discarding real alerts because Azure normalizes identifier casing.
`notify` awaits the provider's test result and saves only mechanism/status/timestamps
in `.local/notification-test.json`; successful dispatch is not proof of human inbox receipt.

```bash
# Read deployed rule queries against the workspace; outputs omit raw log messages.
python3 infra/azure/scripts/monitor.py query failure
python3 infra/azure/scripts/monitor.py query missing-success
python3 infra/azure/scripts/monitor.py query success
python3 infra/azure/scripts/monitor.py status
# Render locally instead, without Azure calls:
python3 infra/azure/scripts/monitor.py query missing-success --render-only

# Explicit external notification API test; verify actual Owner receipt, not just HTTP acceptance.
python3 infra/azure/scripts/monitor.py notify --apply
# Start one labelled Python failure in the existing image; no data access or ingestion heartbeat.
python3 infra/azure/scripts/monitor.py demonstrate-failure --apply
# Wait for log ingestion/evaluation, then inspect failure query, Fired state, and actual delivery.

# Force an observable dead-man interval without inventing a successful ingestion:
python3 infra/azure/scripts/monitor.py demonstrate-deadman --apply
# Do not start ingestion; wait >5 minutes since any real success plus evaluation/ingestion latency.
python3 infra/azure/scripts/monitor.py query missing-success
python3 infra/azure/scripts/monitor.py status
# Restore the original rule properties after collecting Fired/delivery evidence:
python3 infra/azure/scripts/monitor.py restore-deadman --apply
```

The dead-man demonstration changes **only the AQL rule**, saves original properties in
`.local/deadman-restore.json`, and requires explicit restore. The file is retained after
API failure/interruption so restoration is possible; do not redeploy foundation while
an override is active. A stateful already-Fired alert may not send a new notification
until it resolves and fires again. Capture rule state, timestamps, completion
sequence/head, and actual receiver delivery; API tests are explicitly synthetic and
never masquerade as successful SEC ingestion. These external tests are operator actions,
not executed as part of template validation.

## 6. Protected GitHub OIDC run-only workflow

Before enabling `.github/workflows/recorder.yml`, a repository administrator must:

1. Protect the repository's **actual default branch** and merge the reviewed workflow,
   scripts, and built code there. The workflow rejects other refs and has no cron.
2. Create/protect environment `azure-production`, require trusted reviewers, disallow
   self-approval where available, and restrict deployments to the protected default
   branch. The OIDC environment subject alone does not constrain the branch.
3. Set environment variables `AQL_AZURE_CLIENT_ID` = foundation `githubClientId` and
   `AQL_AZURE_TENANT_ID` = foundation `tenantId`. These are not secrets.
4. Set **repository-level** `AQL_ACCEPTANCE_ENABLED=false` initially. It must be
   repository-level because `jobs.if` is evaluated before environment variables load.
   Enable it only for approved manual acceptance; keep false otherwise.
5. Remove/retire obsolete self-hosted recorder configuration only after checking it is
   not used elsewhere. This workflow neither needs nor reads old database/hook secrets.

Only after steps 1-4 have been verified, set `githubRunnerEnabled=true` in the
runtime parameters and redeploy to grant the narrow job role. It defaults false
because an environment-named federation alone does not prove environment protection.
The current token cannot create/protect the environment or set variables; the
provisioned identity therefore has no Azure job-execution permission.
On runtime apply with this flag false, the helper also removes its own previously
created job-scoped GitHub assignment if present; incremental ARM alone would retain
an omitted assignment. It refuses a mismatched principal rather than deleting an
unrelated grant. What-if explicitly reports this revocation intent.

With an authorized GitHub administrative token (the discovery token returned HTTP 403
for Actions variables/secrets; no configuration success is assumed):

```bash
gh variable set AQL_AZURE_CLIENT_ID --repo BruceGK/agentic-quant-lab --env azure-production \
  --body "$(jq -r '.githubClientId.value' infra/azure/.local/foundation.outputs.json)"
gh variable set AQL_AZURE_TENANT_ID --repo BruceGK/agentic-quant-lab --env azure-production \
  --body "$(jq -r '.tenantId.value' infra/azure/.local/foundation.outputs.json)"
gh variable set AQL_ACCEPTANCE_ENABLED --repo BruceGK/agentic-quant-lab --body false
# After verified branch/environment protection and operator approval:
gh variable set AQL_ACCEPTANCE_ENABLED --repo BruceGK/agentic-quant-lab --body true
DEFAULT_BRANCH="$(gh api repos/BruceGK/agentic-quant-lab --jq .default_branch)"
gh workflow run recorder.yml --repo BruceGK/agentic-quant-lab --ref "$DEFAULT_BRANCH" \
  --field confirm_acceptance=true --field command=record
```

Workflow has only checkout read and job-local `id-token: write`, SHA-pinned checkout and
Azure login, a hosted runner, and no application dependency install, build, deployment,
SEC contact, production DSN secret, or artifact containing data. Its output explicitly
does **not** equate job status to verified ingestion. OIDC propagation, environment
protection, scoped role propagation, and a successful real dispatch all require parent
verification.

## Local validation and remaining live gates

```bash
mkdir -p infra/azure/.build
az bicep build --subscription ccc5a11c-86d7-40f1-b02c-58660a2582a7 \
  --file infra/azure/foundation.bicep --outfile infra/azure/.build/foundation.json
az bicep build --subscription ccc5a11c-86d7-40f1-b02c-58660a2582a7 \
  --file infra/azure/runtime.bicep --outfile infra/azure/.build/runtime.json
az bicep build --subscription ccc5a11c-86d7-40f1-b02c-58660a2582a7 \
  --file infra/azure/network.bicep --outfile infra/azure/.build/network.json
az bicep build --subscription ccc5a11c-86d7-40f1-b02c-58660a2582a7 \
  --file infra/azure/cost.bicep --outfile infra/azure/.build/cost.json
bash -n infra/azure/deploy.sh
uv run --frozen ruff check infra/azure
uv run --frozen ruff format --check infra/azure
uv run --frozen pytest infra/azure/tests -q
```

Local tests mock all Azure calls and need no live cloud resources or new test framework.
They cover subscription pinning/redaction, IP and image safety, authoritative migration
receipts/drift refusal, manual job concurrency, and the completion/alert-test boundary.
They do not certify service APIs, pricing, remote KQL schema, or identity propagation.

**Remaining acceptance gates:** genuine SEC contact and actual ingestion, prospective
filing timestamps, duplicate-free official filing rerun and missed-interval recovery.
GitHub dispatch separately requires protected environment/default branch configuration
and an authorized administrative token; it is not required for manual Azure acceptance.
Current credit and actual billing-meter applicability remain operator cost checks.
Use [the deployment report](../../docs/azure-deployment-report.md) for exact live results;
no “Phase 0 complete,” recurring
activation or Phase-1/live-execution claim follows from infrastructure validation.

The later [SEC acceptance report](../../docs/sec-acceptance-report.md) documents
the genuine official-filing gates passing after the secret was configured.
It does not authorize recurring activation; the job remains Manual.
