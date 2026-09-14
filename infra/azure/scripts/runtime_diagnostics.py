"""Read-only in-container checks. Print stages and error codes, never provider messages."""

import ipaddress
import json
import socket
import sys
from urllib.request import urlopen

import psycopg
from azure.core.exceptions import AzureError, HttpResponseError
from psycopg.conninfo import conninfo_to_dict

from agentic_quant_lab.blob_ledger import BlobLedger
from agentic_quant_lab.config import Settings
from agentic_quant_lab.database import connect_database
from agentic_quant_lab.evidence import verify_evidence


def main() -> None:
    stage = "configuration"
    try:
        settings = Settings.from_env(require_sec=False)
        if settings.azure_ledger is None:
            raise ValueError("Azure ledger configuration required")
        stage = "private-dns"
        host = conninfo_to_dict(settings.database_url).get("host")
        if not isinstance(host, str):
            raise ValueError("An explicit PostgreSQL host is required")
        addresses = sorted(
            {result[4][0] for result in socket.getaddrinfo(host, 5432, socket.AF_INET)}
        )
        if not addresses or not all(
            ipaddress.ip_address(address).is_private for address in addresses
        ):
            raise ValueError("PostgreSQL must resolve through the private endpoint")
        print(
            json.dumps({"event": "aql.diagnostics.private-dns", "addresses": addresses}), flush=True
        )
        stage = "egress"
        with urlopen("https://api.ipify.org", timeout=20) as response:
            address = ipaddress.IPv4Address(response.read(64).decode().strip())
        print(json.dumps({"event": "aql.network.egress", "ipv4": str(address)}), flush=True)
        stage = "postgres"
        with connect_database(settings) as connection:
            row = connection.execute("SELECT current_user, current_database()").fetchone()
            if row is None:
                raise RuntimeError("PostgreSQL identity query returned no row")
            print(
                json.dumps(
                    {"event": "aql.diagnostics.postgres", "role": row[0], "database": row[1]}
                ),
                flush=True,
            )
        stage = "blob"
        with BlobLedger(settings.azure_ledger) as ledger:
            verify_evidence(ledger.records)
            print(
                json.dumps({"event": "aql.diagnostics.blob", "records": len(ledger.records)}),
                flush=True,
            )
    except (AzureError, psycopg.Error, OSError, ValueError, KeyError, RuntimeError) as error:
        print(
            json.dumps(
                {
                    "event": "aql.diagnostics.failure",
                    "status": "failed",
                    "stage": stage,
                    "errorType": type(error).__name__,
                    "sqlstate": error.sqlstate if isinstance(error, psycopg.Error) else None,
                    "httpStatus": error.status_code
                    if isinstance(error, HttpResponseError)
                    else None,
                }
            ),
            file=sys.stderr,
            flush=True,
        )
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
