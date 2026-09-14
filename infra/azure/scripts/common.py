"""Small, subscription-pinned operator helpers. Provider output is never an error message."""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any
from uuid import UUID

SUBSCRIPTION = "ccc5a11c-86d7-40f1-b02c-58660a2582a7"
GROUP = "aql-phase0"
GROUP_ID = f"/subscriptions/{SUBSCRIPTION}/resourceGroups/{GROUP}"
JOB_NAME = "aql-recorder"
JOB_ID = f"{GROUP_ID}/providers/Microsoft.App/jobs/{JOB_NAME}"
JOB_API = "2025-01-01"
PG_API = "2024-08-01"
MONITOR_API = "2023-12-01"
WORKSPACE_CUSTOMER_ID = "c75d8583-dbe6-4e57-9cd5-70097059f1ce"
WORKSPACE_ID = (
    f"/subscriptions/{SUBSCRIPTION}/resourceGroups/RiskPulse"
    "/providers/Microsoft.OperationalInsights/workspaces/workspaceriskpulsebaaf"
)
AZURE_DIR = Path(__file__).resolve().parents[1]
ROOT = AZURE_DIR.parent.parent
LOCAL = AZURE_DIR / ".local"
FOUNDATION_OUTPUTS = LOCAL / "foundation.outputs.json"
OWNER_ROLE = "8e3af657-a8ff-443c-a75c-2fe8c4bcb635"


class SafeError(Exception):
    """Only messages written by these scripts, never raw provider/driver exceptions."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SafeError(message)


def local_path(path: Path) -> Path:
    resolved = path.resolve()
    require(resolved.is_relative_to(ROOT), "Files must stay inside the repository.")
    return resolved


def write_json(path: Path, value: Any, *, exclusive: bool = False) -> None:
    path = local_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW
    flags |= os.O_EXCL if exclusive else os.O_TRUNC
    descriptor = os.open(path, flags, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        os.fchmod(stream.fileno(), 0o600)
        json.dump(value, stream, indent=2)
        stream.write("\n")


def emit(value: Any) -> None:
    print(json.dumps(value, indent=2))


def _az(arguments: list[str], *, output: str = "json") -> Any:
    require(
        all(arg != "--subscription" and not arg.startswith("--subscription=") for arg in arguments),
        "A caller cannot override the pinned subscription.",
    )
    completed = subprocess.run(
        [
            "az",
            *arguments,
            "--subscription",
            SUBSCRIPTION,
            "--only-show-errors",
            "--output",
            output,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode:
        # CLI/ARM errors can repeat a secure parameter. Emit neither stream nor the argument list.
        raise SafeError(
            "Azure command failed; provider output suppressed. Check its status in Azure."
        )
    if output != "json":
        return completed.stdout.strip()
    return json.loads(completed.stdout) if completed.stdout.strip() else None


def configure_subscription_environment() -> None:
    for variable in ("AZURE_SUBSCRIPTION_ID", "AQL_SUBSCRIPTION_ID"):
        require(
            os.environ.get(variable, SUBSCRIPTION) == SUBSCRIPTION,
            "An environment subscription override does not match the approved subscription.",
        )
    os.environ["AZURE_SUBSCRIPTION_ID"] = SUBSCRIPTION


def guard_subscription() -> dict[str, str]:
    configure_subscription_environment()
    account = _az(["account", "show", "--query", "{id:id,tenantId:tenantId}"])
    require(
        account["id"] == SUBSCRIPTION, "Azure account does not match the approved subscription."
    )
    return account


def azure(*arguments: str, output: str = "json") -> Any:
    guard_subscription()
    return _az(list(arguments), output=output)


def arm_url(resource_id: str, api: str) -> str:
    require(
        resource_id.lower().startswith(f"/subscriptions/{SUBSCRIPTION}/".lower()),
        "ARM resource is outside the approved subscription.",
    )
    return f"https://management.azure.com{resource_id}?api-version={api}"


def arm(method: str, resource_id: str, api: str, body: Any = None) -> Any:
    arguments = ["rest", "--method", method, "--url", arm_url(resource_id, api)]
    if body is not None:
        # Callers may use this for nonsecret bodies only. Deployment contacts use a protected file.
        arguments += ["--body", json.dumps(body)]
    return azure(*arguments)


def uuid_text(value: str) -> str:
    try:
        canonical = str(UUID(value))
    except (ValueError, AttributeError, TypeError):
        raise SafeError("A required object/client/tenant ID is not a UUID.") from None
    require(canonical == value.lower(), "A UUID must use the canonical hyphenated form.")
    return canonical


def read_outputs(path: Path = FOUNDATION_OUTPUTS) -> dict[str, Any]:
    document = json.loads(local_path(path).read_text())
    require(isinstance(document, dict), "Expected an ARM deployment outputs object.")
    values = {key: output["value"] for key, output in document.items()}
    require(values.get("subscriptionId") == SUBSCRIPTION, "Outputs target another subscription.")
    require(values.get("resourceGroupName") == GROUP, "Outputs target another resource group.")
    return values


def foundation_outputs(path: Path = FOUNDATION_OUTPUTS) -> dict[str, Any]:
    values = read_outputs(path)
    storage = values["storageAccountName"]
    postgres = values["postgresServerName"]
    require(bool(re.fullmatch(r"aql[a-z0-9]{13}", storage)), "Unexpected AQL storage account name.")
    require(postgres == f"aql-pg-{storage[3:]}", "Unexpected AQL PostgreSQL server name.")
    require(
        values["postgresServerId"].lower()
        == f"{GROUP_ID}/providers/Microsoft.DBforPostgreSQL/flexibleServers/{postgres}".lower(),
        "PostgreSQL is not the isolated AQL foundation server.",
    )
    require(
        values["postgresHost"] == f"{postgres}.postgres.database.azure.com",
        "Unexpected PostgreSQL endpoint.",
    )
    for field in ("administratorObjectId", "runtimePrincipalId", "runtimeClientId", "tenantId"):
        uuid_text(values[field])
    for field, name in (
        ("runtimeIdentityId", "aql-recorder-runtime"),
        ("githubIdentityId", "aql-github"),
    ):
        require(
            values[field].lower()
            == (
                f"{GROUP_ID}/providers/Microsoft.ManagedIdentity/userAssignedIdentities/{name}"
            ).lower(),
            "Unexpected managed identity scope.",
        )
    return values


def run_safely(main: Any) -> None:
    try:
        configure_subscription_environment()
        main()
    except SafeError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from None
    except KeyboardInterrupt:
        print("Interrupted; no secret or driver output was printed.", file=sys.stderr)
        raise SystemExit(130) from None
    except Exception as error:
        print(
            f"ERROR: {type(error).__name__}; details suppressed to protect credentials.",
            file=sys.stderr,
        )
        raise SystemExit(1) from None
