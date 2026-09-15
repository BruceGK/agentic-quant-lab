"""Start one existing manual job without changing its persistent definition."""

import argparse
import copy
import re
import time
from datetime import date
from pathlib import Path
from typing import Any

from common import (
    AZURE_DIR,
    GROUP_ID,
    JOB_API,
    JOB_ID,
    JOB_NAME,
    SUBSCRIPTION,
    SafeError,
    arm,
    emit,
    require,
    run_safely,
    write_json,
)

TERMINAL = {"Succeeded", "Failed", "Stopped", "Canceled", "Cancelled"}
COMMANDS = (
    "record",
    "catch-up",
    "snapshot",
    "reconcile",
    "replay",
    "verify-blob",
    "probe-egress",
    "probe-connections",
    "probe-sec",
    "probe-sec-directory",
    "inspect-evidence",
    "accept-missed-interval",
)


def read_job() -> dict[str, Any]:
    job = arm("get", JOB_ID, JOB_API)
    properties = job["properties"]
    config = properties["configuration"]
    require(
        config["triggerType"] == "Manual"
        and config["replicaRetryLimit"] == 0
        and config["manualTriggerConfig"]["parallelism"] == 1
        and config["manualTriggerConfig"]["replicaCompletionCount"] == 1
        and config["replicaTimeout"] in (1800, 3600),
        "Job is no longer the approved single-writer, zero-retry manual configuration.",
    )
    runtime_id = (
        f"{GROUP_ID}/providers/Microsoft.ManagedIdentity"
        "/userAssignedIdentities/aql-recorder-runtime"
    )
    identities = {identifier.lower() for identifier in job["identity"]["userAssignedIdentities"]}
    require(identities == {runtime_id.lower()}, "Job does not use only the AQL runtime identity.")
    environment_id = f"{GROUP_ID}/providers/Microsoft.App/managedEnvironments/aql-recorder-env"
    require(
        properties["environmentId"].lower() == environment_id.lower(),
        "Job does not reference the isolated private-network environment.",
    )
    template = properties["template"]
    require(
        len(template["containers"]) == 1 and not template.get("initContainers"),
        "Unexpected sidecar or initialization container.",
    )
    container = template["containers"][0]
    require(
        container["name"] == "recorder"
        and container["resources"]["cpu"] == 0.5
        and container["resources"]["memory"] == "1Gi"
        and not container.get("command"),
        "Unexpected runtime container configuration.",
    )
    environment = {item["name"]: item for item in container["env"]}
    allowed = {
        "RECORDER_RUN_MODE",
        "LEDGER_BACKEND",
        "DATABASE_AUTH",
        "DATABASE_URL",
        "AZURE_CLIENT_ID",
        "AZURE_SUBSCRIPTION_ID",
        "AZURE_STORAGE_ACCOUNT_URL",
        "AZURE_STORAGE_CONTAINER",
        "AZURE_LEDGER_PREFIX",
        "UNIVERSE_CIKS",
        "INGEST_CIKS",
        "CATCHUP_START",
        "RECORDER_GIT_SHA",
        "SEC_USER_AGENT",
    }
    require(environment.keys() <= allowed, "Unexpected environment variables; review manually.")
    require(
        environment.get("AZURE_SUBSCRIPTION_ID", {}).get("value") == SUBSCRIPTION,
        "Job subscription environment does not match the approved subscription.",
    )
    require(
        environment["RECORDER_RUN_MODE"].get("value") == "acceptance"
        and environment["LEDGER_BACKEND"].get("value") == "azure"
        and environment["DATABASE_AUTH"].get("value") == "azure",
        "Job no longer uses the Azure acceptance-only policy.",
    )
    image_pattern = (
        r"riskpulseacr12345\.azurecr\.io/aql-recorder"
        r"(?:@sha256:[0-9a-f]{64}|:git-[0-9a-f]{40})"
    )
    require(bool(re.fullmatch(image_pattern, container["image"])), "Job image is not pinned.")
    require(
        "password=" not in environment["DATABASE_URL"].get("value", "").lower()
        and (
            "SEC_USER_AGENT" not in environment
            or (
                environment["SEC_USER_AGENT"].get("secretRef") == "sec-user-agent"
                and not environment["SEC_USER_AGENT"].get("value")
            )
        ),
        "Inline database/contact credentials are not allowed.",
    )
    return job


def executions() -> list[dict[str, Any]]:
    return arm("get", f"{JOB_ID}/executions", JOB_API).get("value", [])


def start_execution(
    arguments: list[str],
    *,
    wait: bool,
    failure_demonstration: bool = False,
) -> dict[str, Any]:
    job = read_job()
    before = executions()
    require(
        all(execution.get("properties", {}).get("status") in TERMINAL for execution in before),
        "An execution is active or has unknown status; do not start another writer.",
    )
    original = job["properties"]["template"]["containers"][0]
    container = {key: copy.deepcopy(original[key]) for key in ("name", "image", "resources", "env")}
    container["args"] = arguments
    if arguments == ["probe-connections"]:
        container["command"] = ["python"]
        container["args"] = ["-c", (AZURE_DIR / "scripts/runtime_diagnostics.py").read_text()]
    if arguments in (["probe-sec"], ["probe-sec-directory"]):
        container["command"] = ["python"]
        container["args"] = ["-c", (AZURE_DIR / "scripts/sec_diagnostics.py").read_text()]
        if arguments == ["probe-sec-directory"]:
            container["args"].append("--directory-only")
    if arguments == ["inspect-evidence"]:
        container["command"] = ["python"]
        container["args"] = ["-c", (AZURE_DIR / "scripts/inspect_evidence.py").read_text()]
    if arguments == ["accept-missed-interval"]:
        container["command"] = ["python"]
        container["args"] = ["-c", (AZURE_DIR / "scripts/live_sec_acceptance.py").read_text()]
    if arguments in (["probe-connections"], ["inspect-evidence"]):
        container["env"] = [item for item in container["env"] if item["name"] != "SEC_USER_AGENT"]
    if arguments == ["probe-egress"]:
        container["env"] = []
        container["command"] = ["python"]
        container["args"] = [
            "-c",
            "import ipaddress,json,urllib.request; "
            "response=urllib.request.urlopen('https://api.ipify.org', timeout=20); "
            "address=ipaddress.IPv4Address(response.read(64).decode().strip()); "
            "assert address.is_global; "
            "print(json.dumps({'event':'aql.network.egress','ipv4':str(address)}), flush=True)",
        ]
    if failure_demonstration:
        # Deliberate labelled failure, no SEC, Blob, PostgreSQL, or successful-ingestion event.
        container["env"] = []
        container["command"] = ["python"]
        container["args"] = [
            "-c",
            "import json,sys; "
            "print(json.dumps({'event':'aql.monitor.acceptance.failure',"
            "'status':'failed','error':'manual_alert_acceptance'}), flush=True); sys.exit(1)",
        ]
    response = arm("post", f"{JOB_ID}/start", JOB_API, {"containers": [container]})
    name = response.get("name") if isinstance(response, dict) else None
    if not name:
        # The API also permits a 202 with no body. Never pick an ambiguous concurrent execution.
        previous = {execution["name"] for execution in before}
        for _ in range(20):
            candidates = [
                execution["name"] for execution in executions() if execution["name"] not in previous
            ]
            require(len(candidates) <= 1, "Concurrent starts detected; inspect manually.")
            if candidates:
                name = candidates[0]
                break
            time.sleep(3)
    require(
        isinstance(name, str) and name.startswith(f"{JOB_NAME}-"), "No unique execution returned."
    )
    if not wait:
        return {"execution": name, "status": "Submitted", "ingestionVerified": False}
    deadline = time.monotonic() + job["properties"]["configuration"]["replicaTimeout"] + 300
    while time.monotonic() < deadline:
        execution = arm("get", f"{JOB_ID}/executions/{name}", JOB_API)
        status = execution["properties"]["status"]
        if status in TERMINAL:
            return {"execution": name, "status": status, "ingestionVerified": False}
        time.sleep(15)
    raise TimeoutError("Execution status did not become terminal.")


def command_arguments(command: str, start: str | None, end: str | None) -> list[str]:
    if command != "catch-up":
        require(start is None and end is None, "Date overrides are only valid for catch-up.")
        return [command]
    if start is None or end is None:
        raise SafeError("Explicit start and end are required.")
    require(
        date.fromisoformat(start) <= date.fromisoformat(end), "Catch-up date range is reversed."
    )
    return ["catch-up", "--start", start, "--end", end]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--command", choices=COMMANDS, default="record")
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--wait", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    arguments = command_arguments(args.command, args.start, args.end)
    if not args.apply:
        emit(
            {
                "jobId": JOB_ID,
                "args": arguments,
                "applied": False,
                "note": "No Azure requests made.",
            }
        )
        return
    result = start_execution(arguments, wait=args.wait)
    if args.receipt is not None:
        write_json(args.receipt, result)
    emit(result)
    if args.wait:
        require(
            result["status"] == "Succeeded",
            "AQL execution did not succeed. Inspect AQL monitoring; raw logs were not printed.",
        )
    print(
        "Execution status is not ingestion proof. Verify the completed event and ledger separately."
    )


if __name__ == "__main__":
    run_safely(main)
