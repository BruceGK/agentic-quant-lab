"""Apply authoritative SQL to the isolated AQL database using the operator's Entra token."""

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import psycopg
from common import (
    FOUNDATION_OUTPUTS,
    LOCAL,
    PG_API,
    ROOT,
    SafeError,
    arm,
    azure,
    emit,
    foundation_outputs,
    guard_subscription,
    require,
    run_safely,
    write_json,
)
from psycopg import sql

RUNTIME = "aql_recorder"
READER = "aql_research_reader"
TABLES = ("audit_events", "discoveries", "filings", "corrections")
VIEWS = ("universe_snapshots", "reconciliations")
MIGRATION_NAMES = ("001_evidence.sql", "002_archive_recovery.sql")
# Same session lock as Recorder: never migrate while the evidence writer is active.
WRITER_LOCK = 728415920001


@dataclass(frozen=True)
class Migration:
    name: str
    checksum: str
    body: bytes


def migrations() -> list[Migration]:
    result = []
    for name in MIGRATION_NAMES:
        raw = (ROOT / "migrations" / name).read_bytes()
        text = raw.decode("utf-8")
        require(
            text.startswith("BEGIN;") and text.rstrip().endswith("COMMIT;"),
            "Migration transaction wrappers changed; review the bootstrap instead of guessing.",
        )
        # Only outer transaction control is replaced, so SQL and its receipt commit atomically.
        body = raw[len(b"BEGIN;") : raw.rindex(b"COMMIT;")]
        result.append(Migration(name, hashlib.sha256(raw).hexdigest(), body))
    return result


def fetch_one(cursor: psycopg.Cursor[Any]) -> tuple[Any, ...]:
    row = cursor.fetchone()
    if row is None:
        raise SafeError("A required database metadata row is missing.")
    return row


def schema_hash(connection: psycopg.Connection[Any]) -> str:
    queries = (
        """SELECT nspname, pg_get_userbyid(nspowner)
           FROM pg_namespace WHERE nspname = 'public' ORDER BY nspname""",
        """SELECT c.relname, c.relkind, pg_get_userbyid(c.relowner),
                  c.relrowsecurity, c.relforcerowsecurity,
                  CASE WHEN c.relkind IN ('v','m') THEN pg_get_viewdef(c.oid, true) END,
                  CASE WHEN c.relkind IN ('i','I') THEN pg_get_indexdef(c.oid) END
           FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
           WHERE n.nspname = 'public' ORDER BY c.relname""",
        """SELECT c.relname, a.attnum, a.attname, format_type(a.atttypid, a.atttypmod),
                  a.attnotnull, a.attidentity, a.attgenerated, a.attisdropped,
                  pg_get_expr(d.adbin, d.adrelid)
           FROM pg_attribute a JOIN pg_class c ON c.oid = a.attrelid
           JOIN pg_namespace n ON n.oid = c.relnamespace
           LEFT JOIN pg_attrdef d ON d.adrelid = a.attrelid AND d.adnum = a.attnum
           WHERE n.nspname = 'public' AND a.attnum > 0
           ORDER BY c.relname, a.attnum""",
        """SELECT c.relname, k.conname, k.contype, k.convalidated,
                  k.condeferrable, k.condeferred, pg_get_constraintdef(k.oid, true)
           FROM pg_constraint k JOIN pg_class c ON c.oid = k.conrelid
           JOIN pg_namespace n ON n.oid = c.relnamespace
           WHERE n.nspname = 'public' ORDER BY c.relname, k.conname""",
        """SELECT c.relname, t.tgname, t.tgenabled, pg_get_triggerdef(t.oid, true)
           FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid
           JOIN pg_namespace n ON n.oid = c.relnamespace
           WHERE n.nspname = 'public' AND NOT t.tgisinternal
           ORDER BY c.relname, t.tgname""",
        """SELECT p.proname, pg_get_function_identity_arguments(p.oid),
                  pg_get_userbyid(p.proowner), p.prosecdef, pg_get_functiondef(p.oid)
           FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
           WHERE n.nspname = 'public' ORDER BY p.proname, 2""",
    )
    definition = [connection.execute(query).fetchall() for query in queries]
    encoded = json.dumps(definition, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(encoded).hexdigest()


def migration_history(
    connection: psycopg.Connection[Any], expected: list[Migration]
) -> list[tuple[str, str, str]]:
    tracked = fetch_one(connection.execute("SELECT to_regclass('aql_admin.schema_migrations')"))[0]
    if tracked is None:
        objects = fetch_one(
            connection.execute(
                """SELECT EXISTS (
                   SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
                   WHERE n.nspname IN ('public', 'aql_admin')
               ) OR EXISTS (
                   SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
                   WHERE n.nspname IN ('public', 'aql_admin')
               ) OR EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'aql_admin')"""
            )
        )[0]
        require(
            not objects, "Untracked existing tables/schema/functions; refusing to adopt or erase."
        )
        return []
    history = connection.execute(
        "SELECT version, sha256, schema_sha256 FROM aql_admin.schema_migrations ORDER BY version"
    ).fetchall()
    require(
        [row[0] for row in history] == [migration.name for migration in expected[: len(history)]]
        and len(history) <= len(expected),
        "Unknown or noncontiguous migration history.",
    )
    require(bool(history), "An empty pre-existing migration receipt table is not trusted.")
    for record, migration in zip(history, expected, strict=False):
        require(
            record[1] == migration.checksum, "Applied migration checksum drift; refusing changes."
        )
    require(history[-1][2] == schema_hash(connection), "Evidence schema drift; refusing changes.")
    return history


def role_exists(connection: psycopg.Connection[Any], name: str) -> bool:
    return bool(connection.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (name,)).fetchone())


def check_role(connection: psycopg.Connection[Any], name: str, *, login: bool) -> None:
    row = fetch_one(
        connection.execute(
            """SELECT rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls,
                  rolinherit, rolcanlogin FROM pg_roles WHERE rolname = %s""",
            (name,),
        )
    )
    require(not any(row[:5]), "AQL data role has elevated server privileges.")
    require(not row[5] and row[6] == login, "AQL role login/inheritance policy does not match.")
    member = connection.execute(
        """SELECT 1 FROM pg_auth_members
           WHERE member = (SELECT oid FROM pg_roles WHERE rolname = %s) LIMIT 1""",
        (name,),
    ).fetchone()
    require(member is None, "AQL data roles must not be members of any other role.")


def entra_mapping(connection: psycopg.Connection[Any], name: str) -> tuple[Any, ...] | None:
    rows = connection.execute(
        "SELECT * FROM pg_catalog.pgaadauth_list_principals(false)"
    ).fetchall()
    return next((row for row in rows if row[0] == name), None)


def prepare_roles(
    connection: psycopg.Connection[Any], outputs: dict[str, Any], *, apply: bool
) -> None:
    admin = entra_mapping(connection, outputs["administratorPrincipalName"])
    require(
        admin is not None
        and admin[2].lower() == outputs["administratorObjectId"].lower()
        and admin[3].lower() == outputs["tenantId"].lower()
        and admin[5] == 1,
        "Administrator Entra mapping does not match the verified operator.",
    )
    if not role_exists(connection, RUNTIME):
        require(apply, "Runtime role is not bootstrapped.")
        connection.execute(
            "SELECT pg_catalog.pgaadauth_create_principal_with_oid("
            "%s, %s, 'service', false, false)",
            (RUNTIME, outputs["runtimePrincipalId"]),
        )
    mapping = entra_mapping(connection, RUNTIME)
    require(
        mapping is not None
        and mapping[1] == "service"
        and mapping[2].lower() == outputs["runtimePrincipalId"].lower()
        and mapping[3].lower() == outputs["tenantId"].lower()
        and mapping[4] == 0
        and mapping[5] == 0,
        "Existing runtime role maps to a different or elevated Entra principal.",
    )
    if not role_exists(connection, READER):
        require(apply, "Research reader role is not bootstrapped.")
        connection.execute(
            sql.SQL("CREATE ROLE {} NOLOGIN NOINHERIT").format(sql.Identifier(READER))
        )
    require(
        entra_mapping(connection, READER) is None,
        "Research reader must remain an unmapped NOLOGIN role, not a live Entra identity.",
    )
    if apply:
        connection.execute(sql.SQL("ALTER ROLE {} NOINHERIT").format(sql.Identifier(RUNTIME)))
    check_role(connection, RUNTIME, login=True)
    check_role(connection, READER, login=False)


def restrict_privileges(connection: psycopg.Connection[Any], database: str, admin: str) -> None:
    principals = sql.SQL(", ").join(
        [sql.SQL("PUBLIC"), sql.Identifier(RUNTIME), sql.Identifier(READER)]
    )
    roles = sql.SQL(", ").join(map(sql.Identifier, (RUNTIME, READER)))
    connection.execute(
        sql.SQL("REVOKE ALL ON DATABASE {} FROM {}").format(sql.Identifier(database), principals)
    )
    connection.execute(
        sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(sql.Identifier(database), roles)
    )
    connection.execute(sql.SQL("REVOKE ALL ON SCHEMA public FROM {}").format(principals))
    connection.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(roles))
    connection.execute(sql.SQL("REVOKE ALL ON SCHEMA aql_admin FROM {}").format(principals))
    for kind in ("TABLES", "SEQUENCES", "FUNCTIONS"):
        for schema in ("public", "aql_admin"):
            connection.execute(
                sql.SQL("REVOKE ALL ON ALL {} IN SCHEMA {} FROM {}").format(
                    sql.SQL(kind), sql.Identifier(schema), principals
                )
            )
        connection.execute(
            sql.SQL("ALTER DEFAULT PRIVILEGES FOR ROLE {} REVOKE ALL ON {} FROM {}").format(
                sql.Identifier(admin), sql.SQL(kind), principals
            )
        )
    tables = sql.SQL(", ").join(sql.Identifier("public", name) for name in TABLES)
    views = sql.SQL(", ").join(sql.Identifier("public", name) for name in VIEWS)
    readable = sql.SQL(", ").join(sql.Identifier("public", name) for name in (*TABLES, *VIEWS))
    connection.execute(
        sql.SQL("GRANT SELECT, INSERT ON {} TO {}").format(tables, sql.Identifier(RUNTIME))
    )
    connection.execute(sql.SQL("GRANT SELECT ON {} TO {}").format(views, sql.Identifier(RUNTIME)))
    connection.execute(sql.SQL("GRANT SELECT ON {} TO {}").format(readable, sql.Identifier(READER)))


def check_privileges(connection: psycopg.Connection[Any], database: str) -> None:
    for role in (RUNTIME, READER):
        check_role(connection, role, login=role == RUNTIME)
        for privilege in ("CREATE", "TEMPORARY"):
            require(
                not fetch_one(
                    connection.execute(
                        "SELECT has_database_privilege(%s, %s, %s)", (role, database, privilege)
                    )
                )[0],
                "AQL data role can create database objects or temporary tables.",
            )
        require(
            fetch_one(
                connection.execute(
                    "SELECT has_database_privilege(%s, %s, 'CONNECT')", (role, database)
                )
            )[0],
            "AQL data role cannot connect to the isolated database.",
        )
        schema = connection.execute(
            """SELECT has_schema_privilege(%s, 'public', 'USAGE'),
                      has_schema_privilege(%s, 'public', 'CREATE'),
                      has_schema_privilege(%s, 'aql_admin', 'USAGE')""",
            (role, role, role),
        ).fetchone()
        require(schema == (True, False, False), "AQL schema permissions do not match the policy.")
        ownership = fetch_one(
            connection.execute(
                """SELECT EXISTS (
                   SELECT 1 FROM pg_class
                   WHERE relowner = (SELECT oid FROM pg_roles WHERE rolname=%s)
               ) OR EXISTS (
                   SELECT 1 FROM pg_namespace
                   WHERE nspowner = (SELECT oid FROM pg_roles WHERE rolname=%s)
               ) OR EXISTS (
                   SELECT 1 FROM pg_database
                   WHERE datdba = (SELECT oid FROM pg_roles WHERE rolname=%s)
               ) OR EXISTS (
                   SELECT 1 FROM pg_proc
                   WHERE proowner = (SELECT oid FROM pg_roles WHERE rolname=%s)
               )""",
                (role, role, role, role),
            )
        )[0]
        require(not ownership, "AQL data role must not own database objects.")
        for name in (*TABLES, *VIEWS, "aql_admin.schema_migrations"):
            table = name if "." in name else f"public.{name}"
            for privilege in (
                "SELECT",
                "INSERT",
                "UPDATE",
                "DELETE",
                "TRUNCATE",
                "REFERENCES",
                "TRIGGER",
            ):
                expected = name in (*TABLES, *VIEWS) and (
                    privilege == "SELECT"
                    or (privilege == "INSERT" and role == RUNTIME and name in TABLES)
                )
                actual, grantable = fetch_one(
                    connection.execute(
                        "SELECT has_table_privilege(%s, %s, %s), has_table_privilege(%s, %s, %s)",
                        (role, table, privilege, role, table, f"{privilege} WITH GRANT OPTION"),
                    )
                )
                require(
                    actual == expected and not grantable,
                    "AQL data/table/grant-option permissions do not match the policy.",
                )


def check_mutation_permissions(connection: psycopg.Connection[Any]) -> list[str]:
    denied = []
    with connection.transaction(force_rollback=True):
        connection.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(RUNTIME)))
        for table in TABLES:
            for verb, command in (
                ("UPDATE", sql.SQL("UPDATE {} SET event_id = event_id")),
                ("DELETE", sql.SQL("DELETE FROM {}")),
                ("TRUNCATE", sql.SQL("TRUNCATE {} CASCADE")),
            ):
                try:
                    with connection.transaction(force_rollback=True):
                        connection.execute(command.format(sql.Identifier(table)))
                except psycopg.errors.InsufficientPrivilege:
                    denied.append(f"{verb} {table}")
                else:
                    raise RuntimeError("Runtime mutation was not rejected by database permissions.")
    return denied


def migrate(
    connection: psycopg.Connection[Any],
    expected: list[Migration],
    database: str,
    admin: str,
) -> None:
    history = migration_history(connection, expected)
    if not history:
        owner = fetch_one(
            connection.execute(
                "SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname = current_database()"
            )
        )[0]
        require(owner in (admin, "azure_pg_admin"), "Unexpected initial AQL database owner.")
        connection.execute(
            sql.SQL("ALTER DATABASE {} OWNER TO {}").format(
                sql.Identifier(database), sql.Identifier(admin)
            )
        )
        connection.execute(sql.SQL("ALTER SCHEMA public OWNER TO {}").format(sql.Identifier(admin)))
        connection.execute(
            sql.SQL("CREATE SCHEMA aql_admin AUTHORIZATION {}").format(sql.Identifier(admin))
        )
        connection.execute(
            """CREATE TABLE aql_admin.schema_migrations (
                   version text PRIMARY KEY,
                   sha256 text NOT NULL CHECK (length(sha256) = 64),
                   schema_sha256 text NOT NULL CHECK (length(schema_sha256) = 64),
                   applied_at timestamptz NOT NULL DEFAULT clock_timestamp()
               )"""
        )
    for migration in expected[len(history) :]:
        connection.execute(migration.body, prepare=False)
        connection.execute(
            "INSERT INTO aql_admin.schema_migrations "
            "(version, sha256, schema_sha256) VALUES (%s,%s,%s)",
            (migration.name, migration.checksum, schema_hash(connection)),
        )
    restrict_privileges(connection, database, admin)
    check_privileges(connection, database)
    migration_history(connection, expected)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outputs", type=Path, default=FOUNDATION_OUTPUTS)
    parser.add_argument("--database", choices=("aql", "aql_test"), default="aql")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument(
        "--check", action="store_true", help="Check schema, identity, grants without DDL."
    )
    args = parser.parse_args()
    outputs = foundation_outputs(args.outputs)
    expected = migrations()
    require(
        args.database == "aql" or outputs.get("testDatabaseName") == "aql_test",
        "The optional isolated test database was not requested in the foundation.",
    )
    require(
        outputs["administratorPrincipalName"] == "aql_migration_admin",
        "Only the isolated migration administrator may bootstrap.",
    )
    if not args.apply and not args.check:
        emit(
            {
                "apply": False,
                "database": args.database,
                "server": outputs["postgresHost"],
                "migrations": [{"name": item.name, "sha256": item.checksum} for item in expected],
                "runtimeRole": RUNTIME,
                "researchRole": f"{READER} NOLOGIN",
                "note": "Local plan only; no Azure token or database connection requested.",
            }
        )
        return
    account = guard_subscription()
    require(
        account["tenantId"] == outputs["tenantId"], "Operator tenant does not match foundation."
    )
    operator = azure("rest", "--url", "https://graph.microsoft.com/v1.0/me?$select=id")
    require(
        operator["id"].lower() == outputs["administratorObjectId"].lower(),
        "Signed-in CLI user is not the configured migration administrator.",
    )
    server = arm("get", outputs["postgresServerId"], PG_API)
    authentication = server["properties"]["authConfig"]
    require(
        server["properties"]["fullyQualifiedDomainName"] == outputs["postgresHost"]
        and server["properties"]["version"] == "16"
        and authentication["activeDirectoryAuth"] == "Enabled"
        and authentication["passwordAuth"] == "Disabled",
        "Server endpoint/version/Entra-only authentication does not match foundation.",
    )
    identity = arm("get", outputs["runtimeIdentityId"], "2023-01-31")
    require(
        identity["properties"]["principalId"] == outputs["runtimePrincipalId"],
        "Runtime identity was replaced; refusing to remap the database role.",
    )
    arm("get", f"{outputs['postgresServerId']}/databases/{args.database}", PG_API)
    token = azure(
        "account",
        "get-access-token",
        "--resource",
        "https://ossrdbms-aad.database.windows.net",
        "--query",
        "accessToken",
        output="tsv",
    )
    connection_options = {
        "host": outputs["postgresHost"],
        "port": 5432,
        "user": outputs["administratorPrincipalName"],
        "password": token,
        "sslmode": "verify-full",
        "sslrootcert": "/etc/ssl/certs/ca-certificates.crt",
        "connect_timeout": 15,
        "autocommit": True,
        "application_name": "aql-migration-bootstrap",
        "options": "-c statement_timeout=120000 -c lock_timeout=15000",
    }
    with psycopg.connect(dbname=args.database, **connection_options) as connection:
        locked = fetch_one(connection.execute("SELECT pg_try_advisory_lock(%s)", (WRITER_LOCK,)))[0]
        require(locked, "Recorder is active; stop starting executions before bootstrapping.")
        history = migration_history(connection, expected)
        # Principal management is performed in the new server's built-in postgres database only.
        with (
            psycopg.connect(dbname="postgres", **connection_options) as management,
            management.transaction(),
        ):
            prepare_roles(management, outputs, apply=args.apply)
        if args.apply:
            with connection.transaction():
                migrate(connection, expected, args.database, outputs["administratorPrincipalName"])
        else:
            require(len(history) == len(expected), "Some authoritative migrations are not applied.")
            check_privileges(connection, args.database)
        mutation_denials = check_mutation_permissions(connection)
        receipt = {
            "database": args.database,
            "server": outputs["postgresHost"],
            "migrations": [{"name": item.name, "sha256": item.checksum} for item in expected],
            "schemaSha256": schema_hash(connection),
            "runtimePrincipalId": outputs["runtimePrincipalId"],
            "permissionsChecked": True,
            "mutationPermissionDenials": mutation_denials,
            "applied": args.apply,
        }
    write_json(LOCAL / f"bootstrap-{args.database}.json", receipt)
    emit(receipt)


if __name__ == "__main__":
    run_safely(main)
