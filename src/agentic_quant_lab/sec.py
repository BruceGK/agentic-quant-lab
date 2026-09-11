import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, date, datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from zoneinfo import ZoneInfo

from agentic_quant_lab.config import normalize_cik

SEC_ORIGIN = "https://www.sec.gov"
EASTERN = ZoneInfo("America/New_York")
ACCESSION = r"\d{10}-\d{2}-\d{6}"
ATOM = "{http://www.w3.org/2005/Atom}"


@dataclass(frozen=True)
class Candidate:
    external_id: str
    cik: str
    document_url: str

    @classmethod
    def from_url(cls, url: str) -> "Candidate":
        parsed = urlsplit(url)
        if (
            parsed.scheme != "https"
            or parsed.netloc != "www.sec.gov"
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("Expected a canonical HTTPS SEC Archives submission URL")
        match = re.fullmatch(
            rf"/Archives/edgar/data/(\d{{1,10}})/(?:\d{{18}}/)?({ACCESSION})\.txt",
            parsed.path,
        )
        if not match:
            raise ValueError("Expected a complete submission .txt URL, not a primary document")
        cik, accession = match.groups()
        cik = normalize_cik(cik)
        return cls(accession, cik, f"{SEC_ORIGIN}/Archives/edgar/data/{cik}/{accession}.txt")


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


class SecClient:
    def __init__(self, user_agent: str, max_bytes: int = 32 * 1024 * 1024):
        self.user_agent = user_agent
        self.max_bytes = max_bytes
        self._last_request = 0.0
        self._opener = build_opener(NoRedirect())

    def get(self, url: str) -> bytes:
        if urlsplit(url).scheme != "https" or urlsplit(url).netloc != "www.sec.gov":
            raise ValueError("Only HTTPS www.sec.gov URLs are allowed")
        for attempt in range(4):
            time.sleep(max(0.0, 0.25 - (time.monotonic() - self._last_request)))
            self._last_request = time.monotonic()
            request = Request(
                url, headers={"User-Agent": self.user_agent, "Accept-Encoding": "identity"}
            )
            try:
                with self._opener.open(request, timeout=45) as response:
                    body = response.read(self.max_bytes + 1)
                if len(body) > self.max_bytes:
                    raise ValueError("SEC response exceeds the recorder's size limit")
                return body
            except HTTPError as exc:
                if exc.code not in (429, 500, 502, 503, 504) or attempt == 3:
                    raise
                retry_after = exc.headers.get("Retry-After", "")
                delay = min(float(retry_after), 120) if retry_after.isdigit() else 2**attempt
                time.sleep(max(delay, 2**attempt))
            except (URLError, TimeoutError):
                if attempt == 3:
                    raise
                time.sleep(2**attempt)
        raise AssertionError("unreachable")

    def latest(self) -> list[Candidate]:
        return parse_latest(
            self.get(
                f"{SEC_ORIGIN}/cgi-bin/browse-edgar?action=getcurrent"
                "&owner=include&count=100&output=atom"
            )
        )

    def daily_index(self, day: date) -> bytes:
        quarter = (day.month - 1) // 3 + 1
        return self.get(
            f"{SEC_ORIGIN}/Archives/edgar/daily-index/{day.year}/QTR{quarter}/"
            f"master.{day:%Y%m%d}.idx"
        )

    def fetch(self, candidate: Candidate) -> bytes:
        return self.get(candidate.document_url)


def parse_latest(body: bytes) -> list[Candidate]:
    root = ET.fromstring(body)
    if root.tag != f"{ATOM}feed":
        raise ValueError("SEC response is not an Atom feed")
    result: list[Candidate] = []
    for entry in root.findall(f"{ATOM}entry"):
        links = entry.findall(f"{ATOM}link")
        url = next(
            (
                link.attrib["href"]
                for link in links
                if link.attrib.get("rel", "alternate") == "alternate"
            ),
            None,
        )
        if url is None:
            raise ValueError("SEC Atom entry has no filing link")
        result.append(Candidate.from_url(re.sub(r"-index\.html?$", ".txt", url)))
    return result


def parse_daily_index(body: bytes, day: date) -> list[Candidate]:
    text = body.decode("latin-1")
    lines = text.splitlines()
    header = "CIK|Company Name|Form Type|Date Filed|Filename"
    if header not in lines:
        raise ValueError("Invalid SEC daily index header")
    result: list[Candidate] = []
    for line in lines[lines.index(header) + 1 :]:
        if not line.strip() or set(line.strip()) == {"-"}:
            continue
        fields = line.split("|")
        if len(fields) != 5:
            raise ValueError("Malformed SEC daily index row")
        cik, _, _, filed, path = fields
        if date.fromisoformat(filed) != day:
            raise ValueError("Daily index contains an unexpected filing date")
        candidate = Candidate.from_url(f"{SEC_ORIGIN}/Archives/{path}")
        if candidate.cik != normalize_cik(cik):
            raise ValueError("Daily index CIK/path mismatch")
        result.append(candidate)
    return result


def submission_metadata(body: bytes, candidate: Candidate) -> tuple[datetime, str]:
    header, separator, _ = body.partition(b"</SEC-HEADER>")
    if not separator:
        raise ValueError("Missing complete SEC submission header")
    text = header.decode("latin-1")
    accession = re.search(rf"ACCESSION NUMBER:\s*({ACCESSION})", text)
    accepted = re.search(r"<ACCEPTANCE-DATETIME>(\d{14})", text)
    form = re.search(r"CONFORMED SUBMISSION TYPE:\s*([^\r\n]+)", text)
    if not accession or accession[1] != candidate.external_id or not accepted or not form:
        raise ValueError("Missing or inconsistent SEC submission metadata")
    local = datetime.strptime(accepted[1], "%Y%m%d%H%M%S")
    early, late = local.replace(tzinfo=EASTERN, fold=0), local.replace(tzinfo=EASTERN, fold=1)
    if early.utcoffset() != late.utcoffset():
        raise ValueError("Ambiguous or nonexistent SEC acceptance time")
    if not body.rstrip().endswith(b"</SEC-DOCUMENT>"):
        raise ValueError("Truncated SEC submission")
    return early.astimezone(UTC), form[1].strip()
