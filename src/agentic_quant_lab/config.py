import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit


@dataclass(frozen=True)
class Settings:
    database_url: str
    ledger_path: Path
    sec_user_agent: str
    universe_ciks: tuple[str, ...] = ()
    catchup_start: date | None = None
    heartbeat_url: str | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        database_url = os.environ["DATABASE_URL"]
        user_agent = os.environ["SEC_USER_AGENT"].strip()
        if "@" not in user_agent or "\n" in user_agent or "\r" in user_agent:
            raise ValueError("SEC_USER_AGENT must identify your application and contact email")
        ciks = tuple(
            sorted(
                {normalize_cik(c) for c in os.getenv("UNIVERSE_CIKS", "").split(",") if c.strip()}
            )
        )
        start = os.getenv("CATCHUP_START")
        heartbeat = os.getenv("HEARTBEAT_URL") or None
        if heartbeat and urlsplit(heartbeat).scheme != "https":
            raise ValueError("HEARTBEAT_URL must use HTTPS")
        return cls(
            database_url=database_url,
            ledger_path=Path(os.getenv("LEDGER_PATH", "state/sec.jsonl")).resolve(),
            sec_user_agent=user_agent,
            universe_ciks=ciks,
            catchup_start=date.fromisoformat(start) if start else None,
            heartbeat_url=heartbeat,
        )


def normalize_cik(value: str) -> str:
    value = value.strip()
    if not value.isascii() or not value.isdigit() or not 0 < int(value) < 10**10:
        raise ValueError("CIKs must be positive numbers of at most ten digits")
    return str(int(value))
