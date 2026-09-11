import hashlib
from importlib.metadata import version
from pathlib import Path
from typing import Any

from agentic_quant_lab.config import Settings
from agentic_quant_lab.ledger import digest


def provenance(settings: Settings) -> dict[str, Any]:
    package = Path(__file__).resolve().parent
    source = hashlib.sha256()
    for path in sorted([*package.glob("*.py"), *package.glob("*.toml")]):
        source.update(path.name.encode() + b"\0" + path.read_bytes() + b"\0")
    config = {
        "universe_ciks": sorted(set(settings.universe_ciks)),
        "ingestion_ciks": sorted(set(settings.ingestion_scope)),
        "catchup_start": settings.catchup_start.isoformat() if settings.catchup_start else None,
        "availability_mode": "observed",
        "screen_version": "explicit-cik-list-v1",
    }
    return {
        "package_version": version("agentic-quant-lab"),
        "source_tree_sha256": source.hexdigest(),
        "git_sha": settings.git_sha,
        "config": config,
        "config_sha256": digest(config),
    }
