import os
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import LiteralString, cast
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import make_conninfo

from agentic_quant_lab.config import Settings
from agentic_quant_lab.sec import Candidate, SecClient

URL = "https://www.sec.gov/Archives/edgar/data/320193/0000320193-24-000123.txt"
CANDIDATE = Candidate.from_url(URL)
SUBMISSION = b"""<SEC-DOCUMENT>0000320193-24-000123.txt
<SEC-HEADER>
<ACCEPTANCE-DATETIME>20241101060136
ACCESSION NUMBER: 0000320193-24-000123
CONFORMED SUBMISSION TYPE: 10-K
CENTRAL INDEX KEY: 0000320193
</SEC-HEADER>
<DOCUMENT>Synthetic test content, not a real SEC filing.</DOCUMENT>
</SEC-DOCUMENT>
"""


class FakeSec(SecClient):
    def __init__(self):
        super().__init__("quant-tests test@example.invalid")
        self.content = SUBMISSION
        self.fetch_count = 0
        self.fail = False
        self.indexes: dict[str, bytes] = {}
        self.latest_candidates: list[Candidate] = []
        self.index_requests: list[str] = []

    def fetch(self, candidate: Candidate) -> bytes:
        self.fetch_count += 1
        if self.fail:
            raise TimeoutError("simulated SEC outage")
        return self.content.replace(CANDIDATE.external_id.encode(), candidate.external_id.encode())

    def latest(self) -> list[Candidate]:
        return self.latest_candidates

    def daily_index(self, day) -> bytes:
        self.index_requests.append(day.isoformat())
        return self.indexes[day.isoformat()]


@dataclass
class DatabaseConfig:
    writer_dsn: str
    admin_dsn: str


@pytest.fixture
def database() -> Iterator[DatabaseConfig]:
    dsn = os.getenv("TEST_DATABASE_URL")
    if not dsn:
        pytest.skip("Set TEST_DATABASE_URL to an isolated PostgreSQL database")
    suffix = uuid4().hex
    schema, role = f"test_{suffix}", f"writer_{suffix}"
    admin_dsn = make_conninfo(dsn, options=f"-csearch_path={schema}")
    with psycopg.connect(dsn, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        admin.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(role)))
    try:
        with psycopg.connect(admin_dsn, autocommit=True) as admin:
            migrations = Path(__file__).resolve().parents[1] / "migrations"
            for migration in sorted(migrations.glob("*.sql")):
                admin.execute(cast(LiteralString, migration.read_text()))
            admin.execute(
                sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                    sql.Identifier(schema), sql.Identifier(role)
                )
            )
            admin.execute(
                sql.SQL("GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA {} TO {}").format(
                    sql.Identifier(schema), sql.Identifier(role)
                )
            )
        yield DatabaseConfig(
            make_conninfo(dsn, options=f"-csearch_path={schema} -crole={role}"), admin_dsn
        )
    finally:
        with psycopg.connect(dsn, autocommit=True) as admin:
            admin.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
            admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))


@pytest.fixture
def settings(database: DatabaseConfig, tmp_path: Path) -> Settings:
    return Settings(
        database_url=database.writer_dsn,
        ledger_path=tmp_path / "evidence.jsonl",
        sec_user_agent="quant-tests test@example.invalid",
        universe_ciks=("320193",),
    )
