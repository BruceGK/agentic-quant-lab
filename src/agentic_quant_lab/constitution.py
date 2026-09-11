import tomllib
from importlib.resources import files
from typing import Any


def constitution() -> dict[str, Any]:
    return tomllib.loads(
        files("agentic_quant_lab").joinpath("constitution.toml").read_text(encoding="utf-8")
    )


def check_recording_policy(mode: str) -> None:
    policy = constitution()
    if policy["live_execution"]["enabled"] or policy["research"]["real_alpha_research_enabled"]:
        raise ValueError("This package supports recording and synthetic controls only")
    if mode not in ("local", "acceptance", "scheduled"):
        raise ValueError("Unknown recorder run mode")
    if mode == "scheduled" and not (
        policy["phase0"]["scheduled_recording_enabled"]
        and policy["phase0"]["external_acceptance_complete"]
    ):
        raise ValueError("Scheduled recording is disabled pending external acceptance")
