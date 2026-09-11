from datetime import UTC, date, datetime

import pytest
from conftest import CANDIDATE, SUBMISSION

from agentic_quant_lab.config import Settings, normalize_cik
from agentic_quant_lab.sec import (
    Candidate,
    parse_daily_index,
    parse_latest,
    scheduled_sec_closure,
    submission_metadata,
)


def test_atom_uses_canonical_complete_submission_url() -> None:
    body = b"""<feed xmlns="http://www.w3.org/2005/Atom">
      <entry><link rel="alternate"
        href="https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/0000320193-24-000123-index.htm"/>
      </entry></feed>"""
    assert parse_latest(body) == [CANDIDATE]


@pytest.mark.parametrize(
    "url",
    [
        "http://www.sec.gov/Archives/edgar/data/320193/0000320193-24-000123.txt",
        "https://example.com/Archives/edgar/data/320193/0000320193-24-000123.txt",
        "https://www.sec.gov/Archives/edgar/data/320193/report.htm",
        CANDIDATE.document_url + "?x=1",
    ],
)
def test_reject_non_submission_urls(url: str) -> None:
    with pytest.raises(ValueError):
        Candidate.from_url(url)


def test_sec_timezone_is_eastern_not_utc() -> None:
    accepted, form = submission_metadata(SUBMISSION, CANDIDATE)
    assert accepted == datetime(2024, 11, 1, 10, 1, 36, tzinfo=UTC)
    assert form == "10-K"
    winter = SUBMISSION.replace(b"20241101060136", b"20241201060136")
    assert submission_metadata(winter, CANDIDATE)[0].hour == 11


@pytest.mark.parametrize(
    "content",
    [
        SUBMISSION.replace(b"0000320193-24-000123", b"0000320193-24-000124"),
        SUBMISSION.replace(b"<ACCEPTANCE-DATETIME>", b"<OTHER-TIME>"),
        SUBMISSION.replace(b"20241101060136", b"20241103013000"),
        SUBMISSION[:-30],
        b"<html>Access denied</html>",
    ],
)
def test_invalid_submission_not_eligible(content: bytes) -> None:
    with pytest.raises(ValueError):
        submission_metadata(content, CANDIDATE)


def test_malformed_index_fails_closed() -> None:
    with pytest.raises(ValueError):
        parse_daily_index(b"<html>Access denied</html>", date(2026, 9, 9))
    with pytest.raises(ValueError):
        parse_daily_index(
            b"CIK|Company Name|Form Type|Date Filed|Filename\nbroken row\n", date(2026, 9, 9)
        )


def test_legacy_index_header_and_compact_date() -> None:
    content = (
        b"CIK|Company Name|Form Type|Date Filed|File Name\n"
        b"320193|Example|10-K|20260909|edgar/data/320193/0000320193-24-000123.txt\n"
    )
    assert parse_daily_index(content, date(2026, 9, 9)) == [CANDIDATE]


@pytest.mark.parametrize(
    "day",
    [
        date(2026, 1, 1),
        date(2026, 1, 19),
        date(2026, 2, 16),
        date(2026, 5, 25),
        date(2026, 6, 19),
        date(2026, 7, 3),
        date(2026, 9, 7),
        date(2026, 10, 12),
        date(2026, 11, 11),
        date(2026, 11, 26),
        date(2026, 12, 25),
        date(2021, 12, 31),
    ],
)
def test_sec_observed_federal_holidays(day: date) -> None:
    assert scheduled_sec_closure(day)


def test_exchange_holidays_are_not_sec_holidays() -> None:
    assert not scheduled_sec_closure(date(2026, 4, 3))  # Good Friday
    assert not scheduled_sec_closure(date(2026, 9, 9))


def test_configuration_requires_contact_and_normalizes_universe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql:///test")
    monkeypatch.setenv("SEC_USER_AGENT", "quant-lab test@example.invalid")
    monkeypatch.setenv("UNIVERSE_CIKS", "0000320193,320193,789019")
    monkeypatch.setenv("CATCHUP_START", "2026-09-01")
    settings = Settings.from_env()
    assert settings.universe_ciks == ("320193", "789019")
    assert settings.catchup_start == date(2026, 9, 1)
    monkeypatch.setenv("SEC_USER_AGENT", "anonymous")
    with pytest.raises(ValueError):
        Settings.from_env()
    with pytest.raises(ValueError):
        normalize_cik("0")
