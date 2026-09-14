import os
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit


@dataclass(frozen=True)
class BlobSettings:
    account_url: str
    container: str = "aql-audit-ledger"
    prefix: str = "sec"

    def __post_init__(self) -> None:
        if not re.fullmatch(r"https://[a-z0-9]{3,24}\.blob\.core\.windows\.net", self.account_url):
            raise ValueError("Use an HTTPS Azure Blob account URL without credentials or a path")
        if (
            not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,61}[a-z0-9]", self.container)
            or "--" in self.container
        ):
            raise ValueError("Invalid Azure Blob container name")
        if not re.fullmatch(r"[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*", self.prefix):
            raise ValueError("Use a nonempty relative ledger prefix without dot segments")

    @classmethod
    def from_env(cls) -> "BlobSettings | None":
        backend = os.getenv("LEDGER_BACKEND", "local")
        if backend == "local":
            return None
        if backend != "azure":
            raise ValueError("LEDGER_BACKEND must be local or azure")
        return cls(
            account_url=os.environ["AZURE_STORAGE_ACCOUNT_URL"],
            container=os.getenv("AZURE_STORAGE_CONTAINER", "aql-audit-ledger"),
            prefix=os.getenv("AZURE_LEDGER_PREFIX", "sec"),
        )


@dataclass(frozen=True)
class Settings:
    database_url: str = field(repr=False)
    ledger_path: Path
    sec_user_agent: str = field(repr=False)
    universe_ciks: tuple[str, ...] = ()
    catchup_start: date | None = None
    heartbeat_url: str | None = field(default=None, repr=False)
    ingestion_ciks: tuple[str, ...] | None = None
    git_sha: str | None = None
    azure_ledger: BlobSettings | None = None
    database_auth: str = "password"

    def __post_init__(self) -> None:
        if self.database_auth not in ("password", "azure"):
            raise ValueError("DATABASE_AUTH must be password or azure")

    @property
    def ingestion_scope(self) -> tuple[str, ...]:
        return self.universe_ciks if self.ingestion_ciks is None else self.ingestion_ciks

    @classmethod
    def from_env(cls, *, require_sec: bool = True) -> "Settings":
        database_url = os.environ["DATABASE_URL"]
        user_agent = os.getenv("SEC_USER_AGENT", "").strip()
        if require_sec and ("@" not in user_agent or "\n" in user_agent or "\r" in user_agent):
            raise ValueError("SEC_USER_AGENT must identify your application and contact email")
        ciks = tuple(
            sorted(
                {normalize_cik(c) for c in os.getenv("UNIVERSE_CIKS", "").split(",") if c.strip()}
            )
        )
        start = os.getenv("CATCHUP_START")
        heartbeat = os.getenv("HEARTBEAT_URL") or None
        if heartbeat:
            parsed = urlsplit(heartbeat)
            if (
                parsed.scheme != "https"
                or not parsed.hostname
                or parsed.username
                or parsed.password
                or parsed.fragment
                or any(char.isspace() or ord(char) < 32 for char in heartbeat)
            ):
                raise ValueError(
                    "HEARTBEAT_URL must be an HTTPS URL without userinfo or whitespace"
                )
        ingestion = os.getenv("INGEST_CIKS")
        ingestion_ciks = (
            tuple(sorted({normalize_cik(c) for c in ingestion.split(",") if c.strip()}))
            if ingestion is not None
            else None
        )
        if ingestion_ciks is not None and not ingestion_ciks:
            raise ValueError("INGEST_CIKS must not be empty when configured")
        git_sha = os.getenv("RECORDER_GIT_SHA") or None
        if git_sha and (len(git_sha) != 40 or any(c not in "0123456789abcdef" for c in git_sha)):
            raise ValueError("RECORDER_GIT_SHA must be a full lowercase Git commit SHA")
        return cls(
            database_url=database_url,
            ledger_path=Path(os.getenv("LEDGER_PATH", "state/sec.jsonl")).resolve(),
            sec_user_agent=user_agent,
            universe_ciks=ciks,
            catchup_start=date.fromisoformat(start) if start else None,
            heartbeat_url=heartbeat,
            ingestion_ciks=ingestion_ciks,
            git_sha=git_sha,
            azure_ledger=BlobSettings.from_env(),
            database_auth=os.getenv("DATABASE_AUTH", "password"),
        )


def normalize_cik(value: str) -> str:
    value = value.strip()
    if not value.isascii() or not value.isdigit() or not 0 < int(value) < 10**10:
        raise ValueError("CIKs must be positive numbers of at most ten digits")
    return str(int(value))
