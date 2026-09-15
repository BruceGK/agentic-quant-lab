"""Foundation, private network, then manual runtime. Default to ARM what-if."""

import argparse
import ipaddress
import json
import os
import re
import time
from datetime import date
from pathlib import Path
from typing import Any

from common import (
    AZURE_DIR,
    FOUNDATION_OUTPUTS,
    GROUP,
    GROUP_ID,
    JOB_API,
    JOB_ID,
    LOCAL,
    PG_API,
    SUBSCRIPTION,
    SafeError,
    arm,
    azure,
    emit,
    foundation_outputs,
    local_path,
    require,
    run_safely,
    uuid_text,
    write_json,
)

FOUNDATION_KEYS = {
    "location",
    "postgresLocation",
    "administratorObjectId",
    "administratorPrincipalName",
    "operatorIpv4Addresses",
    "environmentOutboundIpv4Addresses",
    "createTestDatabase",
    "staleAfterMinutes",
}
RUNTIME_KEYS = {
    "imageRef",
    "recorderGitSha",
    "catchupStart",
    "universeCiks",
    "ingestCiks",
    "replicaTimeout",
    "githubRunnerEnabled",
    "useExistingSecUserAgentSecret",
}


def parameters(path: Path, phase: str) -> dict[str, Any]:
    document = json.loads(local_path(path).read_text())
    items = document["parameters"]
    require(isinstance(items, dict), "An ARM parameters object is required.")
    require(
        items.keys()
        <= {"foundation": FOUNDATION_KEYS, "network": set(), "runtime": RUNTIME_KEYS}[phase],
        "Unexpected parameter; secrets and generated foundation values do not belong in this file.",
    )
    require(
        all(isinstance(item, dict) and set(item) == {"value"} for item in items.values()),
        "Only literal, nonsecret parameter values are accepted.",
    )
    return {key: item["value"] for key, item in items.items()}


def ipv4(value: str) -> str:
    address = ipaddress.IPv4Address(value)
    require(address.is_global, "Firewall addresses must be individually approved public IPv4s.")
    return str(address)


def validate_foundation(values: dict[str, Any]) -> list[str]:
    uuid_text(values["administratorObjectId"])
    require(
        values.get("administratorPrincipalName", "aql_migration_admin") == "aql_migration_admin",
        "The administrator must use the isolated aql_migration_admin role.",
    )
    require(values.get("location", "eastus2") == "eastus2", "AQL resource group must use eastus2.")
    require(
        values.get("postgresLocation", "centralus") in ("centralus", "westus3"),
        "PostgreSQL region is not approved/eligible.",
    )
    approved = []
    for field in ("operatorIpv4Addresses", "environmentOutboundIpv4Addresses"):
        require(
            isinstance(values[field], list)
            and (field == "environmentOutboundIpv4Addresses" or bool(values[field])),
            "IP arrays are required; at least one operator IPv4 must be approved.",
        )
        approved.extend(ipv4(value) for value in values[field])
    minutes = values.get("staleAfterMinutes", 1440)
    require(
        type(minutes) is int and 5 <= minutes <= 1440, "Stale threshold must be 5–1440 minutes."
    )
    require(
        type(values.get("createTestDatabase", False)) is bool,
        "createTestDatabase must be a boolean.",
    )
    return sorted(set(approved))


def validate_runtime(values: dict[str, Any]) -> None:
    sha = values["recorderGitSha"]
    require(bool(re.fullmatch(r"[0-9a-f]{40}", sha)), "Supply the full lowercase built commit SHA.")
    repository = "riskpulseacr12345.azurecr.io/aql-recorder"
    image = values["imageRef"]
    digest = re.fullmatch(re.escape(repository) + r"@sha256:[0-9a-f]{64}", image)
    require(
        bool(digest) or image == f"{repository}:git-{sha}",
        "Image must be an AQL ACR digest or the matching immutable git-<40hex> tag.",
    )
    if not digest:
        manifest = azure(
            "acr",
            "repository",
            "show",
            "--name",
            "riskpulseacr12345",
            "--image",
            f"aql-recorder:git-{sha}",
        )
        attributes = manifest["changeableAttributes"]
        require(
            attributes.get("writeEnabled") is False and attributes.get("deleteEnabled") is False,
            "A commit tag is not immutable in ACR; pin its digest instead.",
        )
    start = date.fromisoformat(values["catchupStart"])
    require(start <= date.today(), "Catch-up start may not be in the future.")
    for field in ("universeCiks", "ingestCiks"):
        ciks = values.get(field, values.get("universeCiks", "320193"))
        require(
            isinstance(ciks, str) and bool(re.fullmatch(r"[0-9]{1,10}(,[0-9]{1,10})*", ciks)),
            "CIKs must be an explicit comma-separated list of numeric identifiers.",
        )
    require(values.get("replicaTimeout", 1800) in (1800, 3600), "Unsupported replica timeout.")
    require(
        type(values.get("githubRunnerEnabled", False)) is bool,
        "githubRunnerEnabled must be a boolean.",
    )
    require(
        type(values.get("useExistingSecUserAgentSecret", False)) is bool,
        "useExistingSecUserAgentSecret must be a boolean.",
    )


def check_group() -> bool:
    exists = azure("group", "exists", "--name", GROUP)
    if exists:
        group = azure("group", "show", "--name", GROUP)
        require(
            group.get("tags", {}).get("application") == "agentic-quant-lab",
            "Refusing to adopt an existing resource group without AQL ownership tags.",
        )
    return exists


def ensure_provider(namespace: str, *, apply: bool) -> bool:
    state = azure("provider", "show", "--namespace", namespace, "--query", "registrationState")
    if state == "Registered":
        return False
    if apply:
        azure("provider", "register", "--namespace", namespace, "--wait")
    return True


def monitor_providers(*, apply: bool) -> list[str]:
    return [
        namespace
        for namespace in ("Microsoft.AlertsManagement", "Microsoft.ResourceHealth")
        if ensure_provider(namespace, apply=apply)
    ]


def contact_is_configured(job: dict[str, Any]) -> bool:
    properties = job["properties"]
    secrets = properties["configuration"].get("secrets") or []
    variables = [
        variable
        for container in properties["template"]["containers"]
        for variable in container.get("env", [])
    ]
    return any(secret["name"] == "sec-user-agent" for secret in secrets) or any(
        variable["name"] == "SEC_USER_AGENT" for variable in variables
    )


def runtime_contact(values: dict[str, Any], current: dict[str, Any] | None) -> str:
    if values.get("useExistingSecUserAgentSecret", False):
        require(
            current is not None and contact_is_configured(current),
            "The existing SEC job secret must be provisioned before referencing it.",
        )
        # Do not inspect even a locally exported identity in reference-only mode.
        return ""
    contact = os.environ.get("SEC_USER_AGENT", "")
    require(
        not any(character in contact for character in "\r\n\x00"),
        "SEC_USER_AGENT must be a single-line genuine operator contact.",
    )
    require(
        current is None or not contact_is_configured(current) or bool(contact),
        "Use useExistingSecUserAgentSecret=true to preserve the configured job secret.",
    )
    return contact


def patch_existing_secret_runtime(outputs: dict[str, Any]) -> None:
    from job import TERMINAL, executions, read_job

    read_job()
    require(
        all(item.get("properties", {}).get("status") in TERMINAL for item in executions()),
        "An AQL execution is active; wait before updating its runtime.",
    )
    body = outputs["existingSecretRuntimePatch"]["value"]
    properties = body["properties"]
    require(
        set(body) == {"properties"}
        and set(properties) == {"configuration", "template"}
        and "secrets" not in properties["configuration"]
        and properties["configuration"]["triggerType"] == "Manual",
        "Reference-only PATCH must omit secrets and preserve manual execution.",
    )
    containers = properties["template"]["containers"]
    require(
        len(containers) == 1
        and [item for item in containers[0]["env"] if item["name"] == "SEC_USER_AGENT"]
        == [{"name": "SEC_USER_AGENT", "secretRef": "sec-user-agent"}],
        "Reference-only PATCH must map SEC_USER_AGENT to its existing secret.",
    )
    arm("patch", JOB_ID, JOB_API, body)
    for _ in range(60):
        current = arm("get", JOB_ID, JOB_API)
        state = current["properties"]["provisioningState"]
        if state == "Succeeded":
            actual = current["properties"]["template"]["containers"]
            matches = len(actual) == 1 and all(
                actual[0].get(key) == value for key, value in containers[0].items()
            )
            if matches:
                read_job()
                return
        require(state not in ("Failed", "Canceled"), "Azure runtime PATCH failed.")
        time.sleep(5)
    raise SafeError("Azure runtime PATCH did not finish within five minutes.")


def revoke_disabled_github_runner(outputs: dict[str, Any]) -> None:
    assignment = outputs["githubRoleAssignmentId"]["value"]
    require(
        assignment.lower().startswith(
            f"{JOB_ID}/providers/Microsoft.Authorization/roleAssignments/".lower()
        ),
        "GitHub role revocation must target only the AQL job.",
    )
    name = uuid_text(assignment.rsplit("/", 1)[-1])
    matches = azure(
        "role", "assignment", "list", "--scope", JOB_ID, "--query", f"[?name=='{name}']"
    )
    for match in matches:
        require(
            match["id"].lower() == assignment.lower()
            and match["principalId"] == outputs["githubPrincipalId"]["value"],
            "An unexpected principal holds the AQL GitHub assignment; review manually.",
        )
        azure("role", "assignment", "delete", "--ids", match["id"])


def stale_firewalls(approved: list[str], server_id: str | None = None) -> list[str]:
    if server_id is None:
        servers = azure(
            "resource",
            "list",
            "--resource-group",
            GROUP,
            "--resource-type",
            "Microsoft.DBforPostgreSQL/flexibleServers",
            "--query",
            "[].{id:id,name:name}",
        )
        require(len(servers) <= 1, "Multiple PostgreSQL servers exist in AQL; review manually.")
        if not servers:
            return []
        require(
            bool(re.fullmatch(r"aql-pg-[a-z0-9]{13}", servers[0]["name"])),
            "Refusing to touch an unexpected PostgreSQL server.",
        )
        server_id = servers[0]["id"]
    if not isinstance(server_id, str):
        raise SafeError("Azure did not return the isolated PostgreSQL server ID.")
    require(
        server_id.lower().startswith(
            f"{GROUP_ID}/providers/Microsoft.DBforPostgreSQL/flexibleServers/aql-pg-".lower()
        ),
        "Firewall reconciliation must target only the isolated AQL server.",
    )
    rules = arm("get", f"{server_id}/firewallRules", PG_API)["value"]
    stale = []
    for rule in rules:
        settings = rule["properties"]
        start = ipv4(settings["startIpAddress"])
        require(
            start == settings["endIpAddress"] and rule["name"] == f"aql-{start.replace('.', '-')}",
            "Unexpected or broad firewall rule; review manually before any deployment.",
        )
        if start not in approved:
            stale.append(rule["id"])
    return stale


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("foundation", "network", "runtime"))
    parser.add_argument("--parameters", type=Path, required=True)
    parser.add_argument("--foundation-outputs", type=Path, default=FOUNDATION_OUTPUTS)
    parser.add_argument("--outputs", type=Path)
    parser.add_argument(
        "--apply", action="store_true", help="Provision/update; default is what-if."
    )
    args = parser.parse_args()
    values = parameters(args.parameters, args.phase)
    approved = validate_foundation(values) if args.phase == "foundation" else []
    if args.phase == "runtime":
        validate_runtime(values)
    providers = monitor_providers(apply=args.apply) if args.phase == "foundation" else []
    if args.phase == "network" and ensure_provider("Microsoft.Network", apply=args.apply):
        providers.append("Microsoft.Network")
    exists = check_group()
    stale = stale_firewalls(approved) if args.phase == "foundation" and exists else []
    contact = ""
    if args.phase in ("network", "runtime"):
        require(exists, "Apply the foundation first.")
        outputs = foundation_outputs(args.foundation_outputs)
        values |= {
            "postgresServerName": outputs["postgresServerName"],
            "location": outputs["postgresLocation"],
        }
        if args.phase == "runtime":
            values["storageAccountName"] = outputs["storageAccountName"]
    if args.phase == "runtime":
        jobs = azure(
            "resource",
            "list",
            "--resource-group",
            GROUP,
            "--resource-type",
            "Microsoft.App/jobs",
            "--query",
            "[?name=='aql-recorder'].id",
        )
        current = arm("get", JOB_ID, JOB_API) if jobs else None
        contact = runtime_contact(values, current)
        if contact:
            values["secUserAgent"] = contact
    template = AZURE_DIR / f"{args.phase}.bicep"
    parameter_file = LOCAL / f"deployment-{args.phase}-{os.getpid()}.parameters.json"
    require(not parameter_file.exists(), "An intermediate parameter file already exists.")
    write_json(
        parameter_file,
        {"parameters": {key: {"value": value} for key, value in values.items()}},
        exclusive=True,
    )
    try:
        scope = (
            ["sub", "--location", "eastus2"]
            if args.phase == "foundation"
            else ["group", "--resource-group", GROUP]
        )
        command = [
            "deployment",
            scope[0],
            "create" if args.apply else "what-if",
            *scope[1:],
            "--name",
            f"aql-phase0-{args.phase}",
            "--template-file",
            str(template),
            "--parameters",
            f"@{parameter_file}",
        ]
        if args.phase != "foundation":
            command += ["--mode", "Incremental"]
        if args.apply:
            result = azure(*command, "--query", "properties.outputs")
            require(
                result["subscriptionId"]["value"] == SUBSCRIPTION, "Unexpected deployment scope."
            )
            require(result["resourceGroupName"]["value"] == GROUP, "Unexpected deployment group.")
            if args.phase == "runtime" and values.get("useExistingSecUserAgentSecret", False):
                patch_existing_secret_runtime(result)
            output_path = args.outputs or LOCAL / f"{args.phase}.outputs.json"
            write_json(output_path, result)
            if args.phase == "foundation":
                # Incremental ARM deployments do not remove omitted child firewall resources.
                for resource_id in stale_firewalls(approved, result["postgresServerId"]["value"]):
                    arm("delete", resource_id, PG_API)
            if args.phase == "runtime" and not values.get("githubRunnerEnabled", False):
                revoke_disabled_github_runner(result)
            emit(
                {
                    "applied": args.phase,
                    "subscriptionId": SUBSCRIPTION,
                    "outputs": str(local_path(output_path).relative_to(AZURE_DIR.parent.parent)),
                    "recording": "manual-acceptance-only",
                    **(
                        {
                            "secUserAgentConfigured": bool(contact)
                            or values.get("useExistingSecUserAgentSecret", False)
                        }
                        if args.phase == "runtime"
                        else {}
                    ),
                }
            )
        else:
            result = azure(*command, "--result-format", "ResourceIdOnly", "--no-pretty-print")
            emit(
                {
                    "whatIf": args.phase,
                    "changes": [
                        {"resourceId": change["resourceId"], "changeType": change["changeType"]}
                        for change in result.get("changes", [])
                    ],
                    "aqlFirewallRulesToRemoveOnApply": stale,
                    "providersToRegisterOnApply": providers,
                    "githubRunnerRevocationOnApply": (
                        args.phase == "runtime" and not values.get("githubRunnerEnabled", False)
                    ),
                    "existingSecretRuntimePatchOnApply": (
                        args.phase == "runtime"
                        and values.get("useExistingSecUserAgentSecret", False)
                    ),
                    "applied": False,
                }
            )
    finally:
        parameter_file.unlink(missing_ok=True)


if __name__ == "__main__":
    run_safely(main)
