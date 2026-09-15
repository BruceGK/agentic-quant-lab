import json
from datetime import UTC, date, datetime
from email.message import Message
from http.client import HTTPMessage, IncompleteRead
from io import BytesIO
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError
from urllib.request import Request

import pytest
from conftest import CANDIDATE, SUBMISSION

from agentic_quant_lab.config import Settings, normalize_cik
from agentic_quant_lab.sec import (
    Candidate,
    NoRedirect,
    SecClient,
    SecIndexNotPublished,
    closed_day_index_absent,
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
            b"Last Data Received: Sep 09, 2026\n"
            b"CIK|Company Name|Form Type|Date Filed|Filename\nbroken row\n",
            date(2026, 9, 9),
        )


def test_legacy_index_header_and_compact_date() -> None:
    content = (
        b"Last Data Received: Sep 09, 2026\n"
        b"CIK|Company Name|Form Type|Date Filed|File Name\n"
        b"320193|Example|10-K|20260909|edgar/data/320193/0000320193-24-000123.txt\n"
    )
    assert parse_daily_index(content, date(2026, 9, 9)) == [CANDIDATE]


def test_dissemination_index_can_include_older_filing_dates() -> None:
    content = (
        b"Last Data Received: Sep 09, 2026\n"
        b"CIK|Company Name|Form Type|Date Filed|File Name\n"
        b"320193|Example|10-K|20241101|edgar/data/320193/0000320193-24-000123.txt\n"
    )
    assert parse_daily_index(content, date(2026, 9, 9)) == [CANDIDATE]
    with pytest.raises(ValueError, match="dissemination date"):
        parse_daily_index(content, date(2026, 9, 8))


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


def test_sec_transport_retries_rate_limit_with_identifying_headers() -> None:
    client = SecClient("agentic-quant-lab test@example.invalid")
    headers = Message()
    headers["Retry-After"] = "2"
    rate_limited = HTTPError(CANDIDATE.document_url, 429, "rate limited", headers, None)
    response = MagicMock()
    response.__enter__.return_value = response
    response.read.return_value = SUBMISSION
    response.headers = {"Content-Length": str(len(SUBMISSION))}
    with (
        patch.object(client._opener, "open", side_effect=[rate_limited, response]) as request,
        patch("agentic_quant_lab.sec.time.sleep") as sleep,
    ):
        assert client.fetch(CANDIDATE) == SUBMISSION
    assert request.call_count == 2
    sent = request.call_args.args[0]
    assert sent.get_header("User-agent") == client.user_agent
    assert sent.get_header("Accept-encoding") == "identity"
    assert any(call.args == (2,) for call in sleep.call_args_list)


def test_sec_transport_does_not_retry_access_denied() -> None:
    client = SecClient("agentic-quant-lab test@example.invalid")
    denied = HTTPError(CANDIDATE.document_url, 403, "denied", Message(), None)
    with (
        patch.object(client._opener, "open", side_effect=denied) as request,
        pytest.raises(HTTPError),
    ):
        client.fetch(CANDIDATE)
    assert request.call_count == 1


def test_sec_transport_bounds_content_and_destination() -> None:
    client = SecClient("agentic-quant-lab test@example.invalid", max_bytes=2)
    response = MagicMock()
    response.__enter__.return_value = response
    response.headers = {}
    response.read.return_value = b"too large"
    with (
        patch.object(client._opener, "open", return_value=response),
        pytest.raises(ValueError, match="size limit"),
    ):
        client.fetch(CANDIDATE)
    with pytest.raises(ValueError, match="Only HTTPS"):
        client.get("https://example.invalid/submission")
    assert (
        NoRedirect().redirect_request(
            Request(CANDIDATE.document_url),
            BytesIO(),
            302,
            "",
            HTTPMessage(),
            "https://example.invalid",
        )
        is None
    )


def test_sec_transport_retries_truncated_transfer_before_returning() -> None:
    client = SecClient("agentic-quant-lab test@example.invalid")
    response = MagicMock()
    response.__enter__.return_value = response
    response.headers = {"Content-Length": str(len(SUBMISSION))}
    response.read.side_effect = [SUBMISSION[:-30], SUBMISSION]
    with (
        patch.object(client._opener, "open", return_value=response) as request,
        patch("agentic_quant_lab.sec.time.sleep"),
    ):
        assert client.fetch(CANDIDATE) == SUBMISSION
    assert request.call_count == 2


def test_truncated_index_transfer_is_never_returned_as_complete() -> None:
    client = SecClient("agentic-quant-lab test@example.invalid")
    response = MagicMock()
    response.__enter__.return_value = response
    response.headers = {"Content-Length": "999"}
    response.read.return_value = b"CIK|Company Name|Form Type|Date Filed|File Name\n"
    with (
        patch.object(client._opener, "open", return_value=response) as request,
        patch("agentic_quant_lab.sec.time.sleep"),
        pytest.raises(IncompleteRead),
    ):
        client.daily_index(date(2026, 9, 9))
    assert request.call_count == 4


def directory_listing(*names: str, path: str = "daily-index/2026/QTR3/") -> bytes:
    return json.dumps(
        {"directory": {"name": path, "item": [{"name": name, "type": "file"} for name in names]}}
    ).encode()


def test_closed_day_403_requires_official_directory_absence() -> None:
    client = SecClient("quant-tests test@example.invalid")
    missing = HTTPError("https://www.sec.gov/", 403, "denied", Message(), None)
    with patch.object(
        client, "get", side_effect=[missing, directory_listing("master.20260911.idx")]
    ) as request:
        with pytest.raises(SecIndexNotPublished) as absent:
            client.daily_index(date(2026, 9, 12))
    assert absent.value.day == date(2026, 9, 12)
    assert request.call_args_list[1].args == (
        "https://www.sec.gov/Archives/edgar/daily-index/2026/QTR3/index.json",
    )


@pytest.mark.parametrize("day", [date(2026, 9, 10), date(2026, 9, 11)])
def test_weekday_403_is_never_reclassified_as_missing(day: date) -> None:
    client = SecClient("quant-tests test@example.invalid")
    missing = HTTPError("https://www.sec.gov/", 403, "denied", Message(), None)
    with patch.object(client, "get", side_effect=missing) as request, pytest.raises(HTTPError):
        client.daily_index(day)
    assert request.call_count == 1


def test_listed_closed_day_index_access_denied_still_fails() -> None:
    client = SecClient("quant-tests test@example.invalid")
    denied = HTTPError("https://www.sec.gov/", 403, "denied", Message(), None)
    with (
        patch.object(client, "get", side_effect=[denied, directory_listing("master.20260912.idx")]),
        pytest.raises(HTTPError) as error,
    ):
        client.daily_index(date(2026, 9, 12))
    assert error.value is denied


@pytest.mark.parametrize(
    "body",
    [
        b"not-json",
        directory_listing(),
        directory_listing("unrelated.txt"),
        directory_listing("master.20260911.idx", path="daily-index/2026/QTR2/"),
        directory_listing("master.20260911.idx", "master.20260911.idx"),
        directory_listing("master.20260630.idx"),
        directory_listing("../master.20260911.idx"),
    ],
)
def test_invalid_listing_cannot_explain_a_closed_day_403(body: bytes) -> None:
    with pytest.raises(ValueError):
        closed_day_index_absent(body, date(2026, 9, 12))


def test_closure_directory_failure_is_not_suppressed() -> None:
    client = SecClient("quant-tests test@example.invalid")
    denied = HTTPError("https://www.sec.gov/", 403, "denied", Message(), None)
    with (
        patch.object(client, "get", side_effect=[denied, TimeoutError()]),
        pytest.raises(TimeoutError),
    ):
        client.daily_index(date(2026, 9, 12))


def test_directory_absence_never_certifies_a_weekday() -> None:
    with pytest.raises(ValueError, match="business-day"):
        closed_day_index_absent(directory_listing("master.20260910.idx"), date(2026, 9, 11))


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
