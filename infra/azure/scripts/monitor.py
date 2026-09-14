"""Read AQL signals or explicitly demonstrate AQL-only alerting. Never fake ingestion success."""

import argparse
import copy
import json

from common import (
    AZURE_DIR,
    GROUP,
    GROUP_ID,
    LOCAL,
    MONITOR_API,
    OWNER_ROLE,
    SUBSCRIPTION,
    WORKSPACE_CUSTOMER_ID,
    arm,
    arm_url,
    azure,
    emit,
    require,
    run_safely,
    write_json,
)
from job import start_execution

ACTION_GROUP_ID = f"{GROUP_ID}/providers/Microsoft.Insights/actionGroups/aql-phase0-owners"
RULES = {
    "failure": f"{GROUP_ID}/providers/Microsoft.Insights/scheduledQueryRules/aql-recorder-failure",
    "missing-success": (
        f"{GROUP_ID}/providers/Microsoft.Insights/scheduledQueryRules/aql-recorder-missing-success"
    ),
}
RESTORE_FILE = LOCAL / "deadman-restore.json"


def render_query(kind: str, stale_minutes: int = 1440) -> str:
    require(5 <= stale_minutes <= 1440, "Stale threshold must be 5–1440 minutes.")
    source = (AZURE_DIR / "queries" / "job-logs.kql").read_text()
    body = (AZURE_DIR / "queries" / f"{kind}.kql").read_text()
    return f"{source}\n{body}".replace("__JOB_NAME__", "aql-recorder").replace(
        "__STALE_MINUTES__", str(stale_minutes)
    )


def query(kind: str) -> None:
    if kind in RULES:
        rule = arm("get", RULES[kind], MONITOR_API)
        text = rule["properties"]["criteria"]["allOf"][0]["query"]
    else:
        text = render_query(kind)
    result = azure(
        "monitor",
        "log-analytics",
        "query",
        "--workspace",
        WORKSPACE_CUSTOMER_ID,
        "--analytics-query",
        text,
        "--timespan",
        "P2D",
    )
    emit(result)


def status() -> None:
    url = arm_url(
        f"/subscriptions/{SUBSCRIPTION}/providers/Microsoft.AlertsManagement/alerts",
        "2019-03-01",
    )
    alerts = []
    next_page = f"{url}&timeRange=1d&includeContext=true"
    while next_page:
        response = azure("rest", "--url", next_page)
        alerts.extend(response.get("value", []))
        next_page = response.get("nextLink")
        if next_page:
            require(
                next_page.startswith(f"https://management.azure.com/subscriptions/{SUBSCRIPTION}/"),
                "Alert pagination left the approved subscription.",
            )
    result = []
    for rule_id in RULES.values():
        rule = arm("get", rule_id, MONITOR_API)
        properties = rule["properties"]
        result.append(
            {
                "ruleId": rule_id,
                "enabled": properties["enabled"],
                "evaluationFrequency": properties["evaluationFrequency"],
                "alerts": [
                    {
                        "id": alert["id"],
                        "monitorCondition": alert["properties"]["essentials"]["monitorCondition"],
                        "alertState": alert["properties"]["essentials"]["alertState"],
                    }
                    for alert in alerts
                    if alert["properties"]["essentials"]["alertRule"].casefold()
                    in (
                        rule_id.casefold(),
                        rule_id.rsplit("/", 1)[-1].casefold(),
                    )
                ],
            }
        )
    emit(result)


def notify() -> None:
    response = azure(
        "monitor",
        "action-group",
        "test-notifications",
        "create",
        "--resource-group",
        GROUP,
        "--action-group",
        "aql-phase0-owners",
        "--alert-type",
        "logalertv2",
        "--add-action",
        "armrole",
        "subscription-owner",
        OWNER_ROLE,
        "usecommonalertschema",
    )
    require(isinstance(response, dict), "Azure returned no notification test status.")
    receipt = {
        "notificationRequested": True,
        "state": response["state"],
        "completedTime": response.get("completedTime"),
        "actions": [
            {
                "mechanism": action["MechanismType"],
                "status": action["Status"],
                "subState": action.get("SubState"),
                "sendTime": action.get("SendTime"),
            }
            for action in response.get("actionDetails", [])
        ],
        "inboxReceiptVerified": False,
    }
    write_json(LOCAL / "notification-test.json", receipt)
    emit(receipt)


def demonstrate_deadman() -> None:
    require(not RESTORE_FILE.exists(), "A previous dead-man override needs restoring first.")
    rule_id = RULES["missing-success"]
    original = arm("get", rule_id, MONITOR_API)["properties"]
    fields = ("criteria", "overrideQueryTimeRange", "windowSize", "evaluationFrequency", "enabled")
    saved = {"resourceId": rule_id, "properties": {key: original[key] for key in fields}}
    write_json(RESTORE_FILE, saved, exclusive=True)
    changed = copy.deepcopy(saved["properties"])
    changed["criteria"]["allOf"][0]["query"] = render_query("missing-success", 5)
    changed["overrideQueryTimeRange"] = "PT15M"
    changed["enabled"] = True
    arm("patch", rule_id, MONITOR_API, {"properties": changed})
    emit(
        {
            "staleAfterMinutes": 5,
            "ingestionHeartbeatSent": False,
            "restoreRequired": "python3 infra/azure/scripts/monitor.py restore-deadman --apply",
            "note": (
                "Start no ingestion. Wait for staleness and 5-minute evaluation; "
                "verify Fired and delivery."
            ),
        }
    )


def restore_deadman() -> None:
    saved = json.loads(RESTORE_FILE.read_text())
    require(
        saved["resourceId"] == RULES["missing-success"], "Restore receipt is for another resource."
    )
    require(
        set(saved["properties"])
        == {"criteria", "overrideQueryTimeRange", "windowSize", "evaluationFrequency", "enabled"},
        "Unexpected restore receipt fields.",
    )
    arm("patch", saved["resourceId"], MONITOR_API, {"properties": saved["properties"]})
    RESTORE_FILE.unlink()
    emit({"restored": True, "ruleId": saved["resourceId"]})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    read = commands.add_parser("query")
    read.add_argument("kind", choices=("failure", "missing-success", "success"))
    read.add_argument("--render-only", action="store_true")
    read.add_argument("--stale-minutes", type=int, default=1440)
    commands.add_parser("status")
    for name in ("notify", "demonstrate-failure", "demonstrate-deadman", "restore-deadman"):
        command = commands.add_parser(name)
        command.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.command == "query":
        if args.render_only:
            print(render_query(args.kind, args.stale_minutes))
        else:
            query(args.kind)
    elif args.command == "status":
        status()
    elif not args.apply:
        emit({"operation": args.command, "applied": False, "note": "No Azure requests made."})
    elif args.command == "notify":
        notify()
    elif args.command == "demonstrate-failure":
        result = start_execution([], wait=True, failure_demonstration=True)
        emit(result)
        require(result["status"] == "Failed", "The explicit failure demonstration did not fail.")
        print("This was a labelled alert test, never a successful-ingestion event.")
    elif args.command == "demonstrate-deadman":
        demonstrate_deadman()
    elif args.command == "restore-deadman":
        restore_deadman()


if __name__ == "__main__":
    run_safely(main)
