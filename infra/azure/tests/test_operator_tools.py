import hashlib
import json
import os
from datetime import UTC, date, datetime
from email.message import Message
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock
from urllib.error import HTTPError

import bootstrap
import common
import deploy
import inspect_evidence
import job
import live_sec_acceptance
import monitor
import psycopg
import pytest
import runtime_diagnostics
import sec_diagnostics

from agentic_quant_lab.config import BlobSettings, Settings
from agentic_quant_lab.ledger import LedgerError, digest, make_record

REAL_AZ = common._az


@pytest.fixture(autouse=True)
def forbid_real_azure(monkeypatch):
    def blocked(*args, **kwargs):
        pytest.fail("A local infrastructure test attempted to invoke Azure.")

    monkeypatch.setattr(common, "_az", blocked)
    monkeypatch.setenv("AZURE_SUBSCRIPTION_ID", common.SUBSCRIPTION)
    monkeypatch.delenv("AQL_SUBSCRIPTION_ID", raising=False)


@pytest.mark.parametrize(
    "address", ["0.0.0.0", "127.0.0.1", "10.0.0.1", "192.0.2.1", "1.2.3.4/32", "0.0.0.0/0", "::1"]
)
def test_firewall_rejects_broad_private_and_cidr_addresses(address):
    with pytest.raises((common.SafeError, ValueError)):
        deploy.ipv4(address)


def test_exact_single_public_ipv4():
    assert deploy.ipv4("20.40.60.80") == "20.40.60.80"


def test_initial_foundation_denies_unobserved_runtime_egress():
    approved = deploy.validate_foundation(
        {
            "administratorObjectId": "11111111-1111-1111-1111-111111111111",
            "operatorIpv4Addresses": ["20.40.60.80"],
            "environmentOutboundIpv4Addresses": [],
        }
    )
    assert approved == ["20.40.60.80"]


def test_subscription_cannot_be_overridden(monkeypatch):
    monkeypatch.setenv("AZURE_SUBSCRIPTION_ID", "00000000-0000-0000-0000-000000000000")
    with pytest.raises(common.SafeError, match="subscription override"):
        common.guard_subscription()


def test_local_entrypoints_export_subscription_without_cloud_access(monkeypatch):
    monkeypatch.delenv("AZURE_SUBSCRIPTION_ID")
    main = Mock()
    common.run_safely(main)
    assert os.environ["AZURE_SUBSCRIPTION_ID"] == common.SUBSCRIPTION
    main.assert_called_once_with()


def test_every_cli_command_has_explicit_subscription(monkeypatch):
    calls = []

    def execute(command, **kwargs):
        calls.append(command)
        value = (
            {"id": common.SUBSCRIPTION, "tenantId": "tenant"}
            if command[1:3] == ["account", "show"]
            else {"ok": True}
        )
        return SimpleNamespace(returncode=0, stdout=json.dumps(value), stderr="")

    monkeypatch.delenv("AZURE_SUBSCRIPTION_ID", raising=False)
    monkeypatch.delenv("AQL_SUBSCRIPTION_ID", raising=False)
    monkeypatch.setattr(common, "_az", REAL_AZ)
    monkeypatch.setattr(common.subprocess, "run", execute)
    assert common.azure("group", "exists", "--name", common.GROUP) == {"ok": True}
    assert len(calls) == 2
    assert all(
        command[command.index("--subscription") + 1] == common.SUBSCRIPTION for command in calls
    )
    with pytest.raises(common.SafeError, match="cannot override"):
        REAL_AZ(["group", "show", "--subscription", "another-subscription"])


def test_provider_errors_never_repeat_sensitive_output(monkeypatch):
    sentinel = "credential-redaction-sentinel"
    monkeypatch.setattr(
        common.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=1, stdout=sentinel, stderr=sentinel),
    )
    with pytest.raises(common.SafeError) as result:
        REAL_AZ(["deployment", "group", "create"])
    assert sentinel not in str(result.value)


def test_parameters_refuse_secrets_even_in_an_untracked_local_file(monkeypatch):
    document = {"parameters": {"secUserAgent": {"value": "not-a-real-contact"}}}
    monkeypatch.setattr(Path, "read_text", lambda *args, **kwargs: json.dumps(document))
    with pytest.raises(common.SafeError, match="secrets"):
        deploy.parameters(common.LOCAL / "unused.json", "runtime")


def test_digest_requires_no_registry_or_azure_access():
    deploy.validate_runtime(
        {
            "imageRef": "riskpulseacr12345.azurecr.io/aql-recorder@sha256:" + "a" * 64,
            "recorderGitSha": "b" * 40,
            "catchupStart": "2025-01-01",
        }
    )


@pytest.mark.parametrize(
    "write_enabled,delete_enabled", [(True, True), (False, True), (True, False)]
)
def test_commit_tags_must_be_locked_against_update_and_delete(
    monkeypatch, write_enabled, delete_enabled
):
    monkeypatch.setattr(
        deploy,
        "azure",
        lambda *args: {
            "changeableAttributes": {
                "writeEnabled": write_enabled,
                "deleteEnabled": delete_enabled,
            }
        },
    )
    with pytest.raises(common.SafeError, match="not immutable"):
        deploy.validate_runtime(
            {
                "imageRef": "riskpulseacr12345.azurecr.io/aql-recorder:git-" + "b" * 40,
                "recorderGitSha": "b" * 40,
                "catchupStart": "2025-01-01",
            }
        )


def test_migrations_are_the_exact_authoritative_files():
    for migration in bootstrap.migrations():
        raw = (common.ROOT / "migrations" / migration.name).read_bytes()
        text = raw.decode()
        assert migration.checksum == hashlib.sha256(raw).hexdigest()
        assert migration.body == raw[len(b"BEGIN;") : raw.rindex(b"COMMIT;")]
        assert migration.body.decode("utf-8") == text[len("BEGIN;") : text.rindex("COMMIT;")]
    assert [migration.name for migration in bootstrap.migrations()] == [
        "001_evidence.sql",
        "002_archive_recovery.sql",
    ]


def test_untracked_evidence_cannot_be_adopted():
    connection = Mock()
    connection.execute.side_effect = [
        Mock(fetchone=lambda: (None,)),
        Mock(fetchone=lambda: (True,)),
    ]
    with pytest.raises(common.SafeError, match="Untracked"):
        bootstrap.migration_history(connection, bootstrap.migrations())


def test_missing_database_metadata_fails_explicitly():
    cursor = Mock(fetchone=Mock(return_value=None))
    with pytest.raises(common.SafeError, match="metadata row is missing"):
        bootstrap.fetch_one(cursor)


@pytest.mark.parametrize("drift", ["checksum", "schema", "unknown", "gap"])
def test_bootstrap_refuses_migration_or_schema_drift(monkeypatch, drift):
    expected = bootstrap.migrations()
    history = [(item.name, item.checksum, "schema") for item in expected]
    if drift == "checksum":
        history[0] = (expected[0].name, "changed", "schema")
    elif drift == "unknown":
        history.append(("999_unknown.sql", "changed", "schema"))
    elif drift == "gap":
        history = history[1:]
    monkeypatch.setattr(
        bootstrap, "schema_hash", lambda connection: "changed" if drift == "schema" else "schema"
    )
    connection = Mock()
    connection.execute.side_effect = [
        Mock(fetchone=lambda: ("aql_admin.schema_migrations",)),
        Mock(fetchall=lambda: history),
    ]
    with pytest.raises(common.SafeError):
        bootstrap.migration_history(connection, expected)


def test_migration_history_is_idempotent_without_reexecution(monkeypatch):
    expected = bootstrap.migrations()
    history = [(item.name, item.checksum, "schema") for item in expected]
    monkeypatch.setattr(bootstrap, "schema_hash", lambda connection: "schema")
    connection = Mock()
    connection.execute.side_effect = [
        Mock(fetchone=lambda: ("aql_admin.schema_migrations",)),
        Mock(fetchall=lambda: history),
    ]
    assert bootstrap.migration_history(connection, expected) == history
    assert connection.execute.call_count == 2


def approved_job():
    identity = (
        f"{common.GROUP_ID}/providers/Microsoft.ManagedIdentity"
        "/userAssignedIdentities/aql-recorder-runtime"
    )
    return {
        "identity": {"userAssignedIdentities": {identity: {}}},
        "properties": {
            "environmentId": (
                f"{common.GROUP_ID}/providers/Microsoft.App/managedEnvironments/aql-recorder-env"
            ),
            "configuration": {
                "triggerType": "Manual",
                "replicaRetryLimit": 0,
                "replicaTimeout": 1800,
                "manualTriggerConfig": {"parallelism": 1, "replicaCompletionCount": 1},
            },
            "template": {
                "containers": [
                    {
                        "name": "recorder",
                        "resources": {"cpu": 0.5, "memory": "1Gi"},
                        "image": "riskpulseacr12345.azurecr.io/aql-recorder@sha256:" + "a" * 64,
                        "env": [
                            {"name": "RECORDER_RUN_MODE", "value": "acceptance"},
                            {"name": "LEDGER_BACKEND", "value": "azure"},
                            {"name": "DATABASE_AUTH", "value": "azure"},
                            {"name": "AZURE_SUBSCRIPTION_ID", "value": common.SUBSCRIPTION},
                            {"name": "DATABASE_URL", "value": "user=aql_recorder"},
                            {"name": "SEC_USER_AGENT", "secretRef": "sec-user-agent"},
                        ],
                    }
                ]
            },
        },
    }


@pytest.mark.parametrize("demonstration", [False, True])
def test_job_success_never_implies_verified_ingestion(monkeypatch, demonstration):
    calls = []
    responses = iter(
        [
            approved_job(),
            {"value": []},
            {"name": "aql-recorder-example"},
            {"properties": {"status": "Failed" if demonstration else "Succeeded"}},
        ]
    )

    def request(*arguments):
        calls.append(arguments)
        return next(responses)

    monkeypatch.setattr(job, "arm", request)
    result = job.start_execution(["record"], wait=True, failure_demonstration=demonstration)
    assert result["ingestionVerified"] is False
    posted = calls[2][3]["containers"][0]
    if demonstration:
        assert posted["env"] == []
        assert "aql.monitor.acceptance.failure" in posted["args"][1]
        assert "aql.recorder.completed" not in posted["args"][1]
    else:
        assert posted["args"] == ["record"]


def test_running_execution_blocks_another_start(monkeypatch):
    responses = iter([approved_job(), {"value": [{"properties": {"status": "Running"}}]}])
    monkeypatch.setattr(job, "arm", lambda *args: next(responses))
    with pytest.raises(common.SafeError, match="active"):
        job.start_execution(["record"], wait=False)


def test_egress_probe_does_not_receive_recorder_configuration(monkeypatch):
    responses = iter(
        [
            approved_job(),
            {"value": []},
            {"name": "aql-recorder-probe"},
            {"properties": {"status": "Succeeded"}},
        ]
    )
    calls = []

    def request(*arguments):
        calls.append(arguments)
        return next(responses)

    monkeypatch.setattr(job, "arm", request)
    result = job.start_execution(["probe-egress"], wait=True)
    posted = calls[2][3]["containers"][0]
    assert posted["env"] == []
    assert posted["command"] == ["python"]
    assert "aql.network.egress" in posted["args"][1]
    assert "aql.recorder.completed" not in posted["args"][1]
    assert result["ingestionVerified"] is False


@pytest.mark.parametrize("subscription", [None, "00000000-0000-0000-0000-000000000000"])
def test_job_rejects_missing_or_wrong_subscription(monkeypatch, subscription):
    existing = approved_job()
    for variable in existing["properties"]["template"]["containers"][0]["env"]:
        if variable["name"] == "AZURE_SUBSCRIPTION_ID":
            variable["value"] = subscription
    monkeypatch.setattr(job, "arm", lambda *args: existing)
    with pytest.raises(common.SafeError, match="subscription environment"):
        job.read_job()


@pytest.mark.parametrize("secrets", [None, [], [{"name": "sec-user-agent"}]])
def test_contact_reference_is_preserved_even_when_get_hides_secret_names(secrets):
    existing = approved_job()
    existing["properties"]["configuration"]["secrets"] = secrets
    assert deploy.contact_is_configured(existing)


def test_existing_secret_can_be_mapped_without_reading_any_contact_value(monkeypatch):
    existing = approved_job()
    existing["properties"]["configuration"]["secrets"] = [{"name": "sec-user-agent"}]
    existing["properties"]["template"]["containers"][0]["env"] = []
    environment = Mock()
    environment.get.side_effect = AssertionError("Reference mode must not read a contact value")
    with monkeypatch.context() as isolated:
        isolated.setattr(deploy.os, "environ", environment)
        assert deploy.runtime_contact({"useExistingSecUserAgentSecret": True}, existing) == ""


@pytest.mark.parametrize(
    "existing", [None, {"properties": {"configuration": {}, "template": {"containers": []}}}]
)
def test_reference_mode_fails_without_an_existing_job_secret(existing):
    with pytest.raises(common.SafeError, match="must be provisioned"):
        deploy.runtime_contact({"useExistingSecUserAgentSecret": True}, existing)


def test_configured_secret_cannot_be_implicitly_unmapped(monkeypatch):
    monkeypatch.delenv("SEC_USER_AGENT", raising=False)
    with pytest.raises(common.SafeError, match="useExistingSecUserAgentSecret=true"):
        deploy.runtime_contact({}, approved_job())


def test_reference_only_bicep_omits_secret_declarations():
    template = (common.AZURE_DIR / "runtime.bicep").read_text()
    assert "param useExistingSecUserAgentSecret bool = false" in template
    assert "union(runtimeConfiguration, empty(secUserAgent) ? {} : {" in template
    assert "empty(secUserAgent) && !useExistingSecUserAgentSecret ? []" in template
    assert "secretRef: 'sec-user-agent'" in template
    assert "if (!useExistingSecUserAgentSecret)" in template
    assert "output existingSecretRuntimePatch object" in template


def test_reference_runtime_patch_never_reads_or_writes_secret_values(monkeypatch):
    existing = approved_job()
    existing["properties"]["provisioningState"] = "Succeeded"
    properties = {name: existing["properties"][name] for name in ("configuration", "template")}
    monkeypatch.setattr(job, "read_job", lambda: existing)
    monkeypatch.setattr(job, "executions", lambda: [])
    calls = []

    def request(*arguments):
        calls.append(arguments)
        return existing

    monkeypatch.setattr(deploy, "arm", request)
    deploy.patch_existing_secret_runtime(
        {"existingSecretRuntimePatch": {"value": {"properties": properties}}}
    )
    assert calls[0][0:3] == ("patch", common.JOB_ID, common.JOB_API)
    assert "secrets" not in calls[0][3]["properties"]["configuration"]
    assert calls[1] == ("get", common.JOB_ID, common.JOB_API)


def test_reference_runtime_patch_rejects_secret_collection(monkeypatch):
    existing = approved_job()
    existing["properties"]["configuration"]["secrets"] = [{"name": "sec-user-agent"}]
    monkeypatch.setattr(job, "read_job", lambda: existing)
    monkeypatch.setattr(job, "executions", lambda: [])
    request = Mock()
    monkeypatch.setattr(deploy, "arm", request)
    with pytest.raises(common.SafeError, match="omit secrets"):
        deploy.patch_existing_secret_runtime(
            {
                "existingSecretRuntimePatch": {
                    "value": {
                        "properties": {
                            name: existing["properties"][name]
                            for name in ("configuration", "template")
                        }
                    }
                }
            }
        )
    request.assert_not_called()


def test_reference_runtime_patch_waits_for_the_requested_image(monkeypatch):
    existing = approved_job()
    existing["properties"]["provisioningState"] = "Succeeded"
    desired = approved_job()
    desired["properties"]["provisioningState"] = "Succeeded"
    desired["properties"]["template"]["containers"][0]["image"] = (
        "riskpulseacr12345.azurecr.io/aql-recorder@sha256:" + "b" * 64
    )
    monkeypatch.setattr(job, "read_job", lambda: existing)
    monkeypatch.setattr(job, "executions", lambda: [])
    request = Mock(side_effect=[None, existing, desired])
    monkeypatch.setattr(deploy, "arm", request)
    sleep = Mock()
    monkeypatch.setattr(deploy.time, "sleep", sleep)
    deploy.patch_existing_secret_runtime(
        {
            "existingSecretRuntimePatch": {
                "value": {
                    "properties": {
                        name: desired["properties"][name] for name in ("configuration", "template")
                    }
                }
            }
        }
    )
    assert request.call_count == 3
    sleep.assert_called_once_with(5)


def test_sec_diagnostics_log_status_not_contact_headers_or_error_body(monkeypatch, capsys):
    sentinel = "private-contact-sentinel"
    monkeypatch.setattr(
        sec_diagnostics.Settings,
        "from_env",
        lambda: SimpleNamespace(
            sec_user_agent=sentinel, catchup_start=date(2026, 9, 10), ingestion_scope=("320193",)
        ),
    )
    client = Mock()
    client.get.side_effect = HTTPError("https://www.sec.gov/", 403, sentinel, Message(), None)
    monkeypatch.setattr(sec_diagnostics, "SecClient", lambda user_agent: client)
    with pytest.raises(SystemExit) as exited:
        sec_diagnostics.main()
    assert exited.value.code == 1
    output = capsys.readouterr()
    assert sentinel not in output.out + output.err
    records = [json.loads(line) for line in output.out.splitlines()]
    assert len(records) == 9
    assert all(record["httpStatus"] == 403 for record in records)
    assert all(record["status"] == "failed" for record in records)


def test_evidence_inspection_is_read_only_and_excludes_raw_payload(monkeypatch, capsys):
    recorder = MagicMock()
    recorder.__enter__.return_value = recorder
    recorder.ledger.records = [
        {
            "kind": "filing",
            "sequence": 2,
            "hash": "a" * 64,
            "prev_hash": "b" * 64,
            "payload": dict.fromkeys(inspect_evidence.FIELDS, "safe")
            | {"content_base64": "raw-content-sentinel"},
        }
    ]
    factory = Mock(return_value=recorder)
    monkeypatch.setattr(inspect_evidence, "Recorder", factory)
    monkeypatch.setattr(inspect_evidence.Settings, "from_env", lambda **kwargs: Mock())
    inspect_evidence.main()
    assert factory.call_args.kwargs == {"replay": False}
    output = capsys.readouterr().out
    assert "raw-content-sentinel" not in output
    assert "aql.recorder.completed" not in output


def test_missed_interval_uses_isolated_projection_and_no_latest_feed(monkeypatch, tmp_path, capsys):
    settings = Settings(
        "dbname=aql",
        tmp_path / "unused",
        "private-contact-sentinel",
        catchup_start=date(2026, 9, 10),
        azure_ledger=BlobSettings("https://aqltest.blob.core.windows.net"),
    )
    payload = {"source": "sec", "ciks": ["320193"]}
    baseline = make_record([], "universe", {**payload, "universe_hash": digest(payload)})
    records = [
        baseline,
        {
            "kind": "filing",
            "hash": "a" * 64,
            "payload": {
                "external_id": "0000000001-26-000001",
                "first_seen_at": "2026-09-14T00:00:01+00:00",
                "fetched_at": "2026-09-14T00:00:02+00:00",
                "decision_eligible_at": "2026-09-14T00:00:02+00:00",
            },
        },
    ]
    production, empty, recorder = MagicMock(), MagicMock(), MagicMock()
    production.__enter__.return_value.records = [baseline]
    empty.__enter__.return_value.records = []
    recorder.__enter__.return_value = recorder
    recorder.ledger.records = records
    recorder.catch_up.side_effect = [1, 0]
    connection, projection, container, credential = (MagicMock() for _ in range(4))
    monkeypatch.setattr(live_sec_acceptance.Settings, "from_env", lambda: settings)
    monkeypatch.setattr(live_sec_acceptance, "BlobLedger", Mock(side_effect=[production, empty]))
    monkeypatch.setattr(live_sec_acceptance, "connect_database", Mock(return_value=connection))
    monkeypatch.setattr(live_sec_acceptance, "Projection", Mock(return_value=projection))
    monkeypatch.setattr(live_sec_acceptance, "ContainerClient", Mock(return_value=container))
    monkeypatch.setattr(live_sec_acceptance, "azure_credential", Mock(return_value=credential))
    factory = Mock(return_value=recorder)
    monkeypatch.setattr(live_sec_acceptance, "Recorder", factory)
    monkeypatch.setattr(live_sec_acceptance, "utc_now", lambda: datetime(2026, 9, 14, tzinfo=UTC))
    live_sec_acceptance.main()
    target = factory.call_args.args[0]
    assert target.database_url == "dbname=aql_test"
    assert target.azure_ledger.prefix == "acceptance/missed-sec-2026-09-10"
    projection.reconcile.assert_called_once_with([baseline])
    container.__enter__.return_value.upload_blob.assert_called_once()
    assert container.__enter__.return_value.upload_blob.call_args.kwargs["overwrite"] is False
    recorder.record.assert_not_called()
    output = capsys.readouterr().out
    assert "private-contact-sentinel" not in output
    result = json.loads(output)
    assert result["recovered_filings"] == 1
    assert result["rerun_new_filings"] == 0
    assert result["latest_feed_used"] is False


def test_missed_interval_refuses_nonbaseline_database_before_writing(monkeypatch, tmp_path, capsys):
    settings = Settings(
        "dbname=aql",
        tmp_path / "unused",
        "",
        catchup_start=date(2026, 9, 10),
        azure_ledger=BlobSettings("https://aqltest.blob.core.windows.net"),
    )
    payload = {"source": "sec", "ciks": ["320193"]}
    baseline = make_record([], "universe", {**payload, "universe_hash": digest(payload)})
    production = MagicMock()
    production.__enter__.return_value.records = [baseline]
    projection = MagicMock()
    projection.reconcile.side_effect = LedgerError("private-driver-sentinel")
    monkeypatch.setattr(live_sec_acceptance.Settings, "from_env", lambda: settings)
    monkeypatch.setattr(live_sec_acceptance, "BlobLedger", Mock(return_value=production))
    monkeypatch.setattr(live_sec_acceptance, "connect_database", Mock(return_value=MagicMock()))
    monkeypatch.setattr(live_sec_acceptance, "Projection", Mock(return_value=projection))
    upload = Mock()
    monkeypatch.setattr(live_sec_acceptance, "ContainerClient", upload)
    with pytest.raises(SystemExit):
        live_sec_acceptance.main()
    upload.assert_not_called()
    assert "private-driver-sentinel" not in capsys.readouterr().err


def test_deadman_query_includes_never_successful_and_qualified_completion():
    query = monitor.render_query("missing-success", 5)
    assert "datatable(TimeGenerated:datetime, Log_s:string) []" in query
    assert "SuccessfulIngestions = count()" in query
    assert "SuccessfulIngestions == 0" in query
    assert "MissingSuccess = iff(SuccessfulIngestions == 0, 1, 0)" in query
    assert "TimeGenerated = now()" not in query
    assert 'Payload.event) == "aql.recorder.completed"' in query
    assert 'Payload.command) in ("record", "catch-up")' in query
    assert 'Payload.ledger_backend) == "azure"' in query
    assert 'Payload.reconciliation) == "passed"' in query
    assert "ago(5m)" in query
    assert "__JOB_NAME__" not in query and "__STALE_MINUTES__" not in query


def test_blob_urls_do_not_include_the_arm_endpoint_trailing_slash():
    for filename in ("runtime.bicep", "modules/foundation-resources.bicep"):
        template = (common.AZURE_DIR / filename).read_text()
        assert "primaryEndpoints.blob" not in template
        assert "'https://${storage.name}.blob.${environment().suffixes.storage}'" in template


def test_notification_receipt_keeps_only_provider_status_not_destination(monkeypatch):
    monkeypatch.setattr(
        monitor,
        "azure",
        lambda *args: {
            "state": "Complete",
            "completedTime": "2026-09-14T00:00:00Z",
            "actionDetails": [
                {
                    "MechanismType": "Email",
                    "Status": "Succeeded",
                    "SubState": "Default",
                    "SendTime": "2026-09-14T00:00:00Z",
                    "Name": "private contact",
                    "Detail": "private destination",
                }
            ],
        },
    )
    write = Mock()
    monkeypatch.setattr(monitor, "write_json", write)
    monkeypatch.setattr(monitor, "emit", Mock())
    monitor.notify()
    receipt = write.call_args.args[1]
    assert receipt["actions"][0]["status"] == "Succeeded"
    assert receipt["inboxReceiptVerified"] is False
    assert "private" not in json.dumps(receipt)


def test_github_runner_is_not_authorized_by_default():
    template = (common.AZURE_DIR / "runtime.bicep").read_text()
    assert "param githubRunnerEnabled bool = false" in template
    assert "if (githubRunnerEnabled)" in template


def test_entra_admin_waits_for_firewall_updates():
    template = (common.AZURE_DIR / "modules/foundation-resources.bicep").read_text()
    administrator = template.split("resource administrator ", 1)[1].split("resource firewall ", 1)[
        0
    ]
    assert "dependsOn: [\n    firewall\n  ]" in administrator


def test_mutation_probe_requires_actual_permission_denials():
    connection = MagicMock()
    connection.execute.side_effect = [None] + [
        psycopg.errors.InsufficientPrivilege("synthetic denial") for _ in range(12)
    ]
    result = bootstrap.check_mutation_permissions(connection)
    assert len(result) == 12
    assert connection.transaction.call_count == 13
    assert all(
        call.kwargs == {"force_rollback": True} for call in connection.transaction.call_args_list
    )


def test_unexpected_mutation_success_is_rolled_back_and_fails():
    connection = MagicMock()
    with pytest.raises(RuntimeError, match="mutation was not rejected"):
        bootstrap.check_mutation_permissions(connection)
    assert connection.transaction.call_count == 2
    assert connection.transaction.return_value.__exit__.call_count == 2


def test_monitor_provider_preflight_only_registers_on_apply(monkeypatch):
    calls = []

    def request(*arguments):
        calls.append(arguments)
        return "NotRegistered"

    monkeypatch.setattr(deploy, "azure", request)
    assert len(deploy.monitor_providers(apply=False)) == 2
    assert all(call[1] == "show" for call in calls)
    calls.clear()
    assert len(deploy.monitor_providers(apply=True)) == 2
    assert sum(call[1] == "register" for call in calls) == 2


def test_cloud_diagnostics_do_not_log_provider_error_messages(monkeypatch, capsys):
    monkeypatch.setattr(
        runtime_diagnostics.Settings,
        "from_env",
        lambda **kwargs: SimpleNamespace(azure_ledger=object(), database_url="host=test"),
    )
    monkeypatch.setattr(
        runtime_diagnostics.socket,
        "getaddrinfo",
        lambda *args: [(None, None, None, None, ("10.86.0.68", 5432))],
    )
    response = MagicMock()
    response.__enter__.return_value.read.return_value = b"20.40.60.80"
    monkeypatch.setattr(runtime_diagnostics, "urlopen", lambda *args, **kwargs: response)
    monkeypatch.setattr(
        runtime_diagnostics,
        "connect_database",
        Mock(side_effect=psycopg.OperationalError("private-token-sentinel")),
    )
    with pytest.raises(SystemExit) as exit_status:
        runtime_diagnostics.main()
    assert exit_status.value.code == 1
    output = capsys.readouterr()
    assert "private-token-sentinel" not in output.out + output.err
    assert json.loads(output.err)["stage"] == "postgres"


def test_alert_status_normalizes_resource_ids_and_avoids_lossy_filters(monkeypatch):
    rule = monitor.RULES["failure"]
    calls = []

    def request(*arguments):
        calls.append(arguments)
        return {
            "value": [
                {
                    "id": "verified-alert",
                    "properties": {
                        "essentials": {
                            "alertRule": rule.lower(),
                            "monitorCondition": "Fired",
                            "alertState": "New",
                        }
                    },
                }
            ]
        }

    monkeypatch.setattr(monitor, "azure", request)
    monkeypatch.setattr(
        monitor,
        "arm",
        lambda *args: {"properties": {"enabled": True, "evaluationFrequency": "PT5M"}},
    )
    output = Mock()
    monkeypatch.setattr(monitor, "emit", output)
    monitor.status()
    assert output.call_args.args[0][0]["alerts"][0]["monitorCondition"] == "Fired"
    assert output.call_args.args[0][1]["alerts"] == []
    assert len(calls) == 1
    assert "targetResource=" not in calls[0][-1]
    assert "alertRule=" not in calls[0][-1]


def test_disabling_github_removes_only_its_existing_job_assignment(monkeypatch):
    assignment = (
        f"{common.JOB_ID}/providers/Microsoft.Authorization/roleAssignments/"
        "11111111-1111-1111-1111-111111111111"
    )
    principal = "22222222-2222-2222-2222-222222222222"
    calls = []

    def request(*arguments):
        calls.append(arguments)
        if arguments[2] == "list":
            return [{"id": assignment.lower(), "principalId": principal}]

    monkeypatch.setattr(deploy, "azure", request)
    deploy.revoke_disabled_github_runner(
        {
            "githubRoleAssignmentId": {"value": assignment},
            "githubPrincipalId": {"value": principal},
        }
    )
    assert calls[-1] == ("role", "assignment", "delete", "--ids", assignment.lower())
