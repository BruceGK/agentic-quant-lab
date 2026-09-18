"""Validate the committed presentation without installing authoring dependencies."""

import csv
import hashlib
import json
import posixpath
import re
import struct
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import pytest

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo"
DECK = DEMO / "Agentic-Quant-Lab-Demo.pptx"
NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}


@pytest.mark.parametrize(
    "relative",
    [
        "README.md",
        "docs/research-status.md",
        "demo/Agentic-Quant-Lab-Demo.pptx",
        "demo/presentation-script.md",
        "demo/demo-runbook.md",
        "demo/slides.md",
        "demo/demo-output.txt",
        "demo/generate_slides.py",
        "demo/assets/deck-validation.json",
        "demo/assets/offline-demo/index.html",
        "demo/assets/offline-demo/receipt.json",
        "demo/assets/offline-demo/result.json",
    ],
)
def test_required_demo_package(relative: str) -> None:
    path = ROOT / relative
    assert path.is_file(), f"Missing required demo artifact: {relative}"
    assert path.stat().st_size > 0


def test_pptx_is_widescreen_with_eleven_self_contained_slides() -> None:
    with zipfile.ZipFile(DECK) as archive:
        assert archive.testzip() is None
        names = set(archive.namelist())
        assert len(names) == len(archive.namelist())
        slides = {name for name in names if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)}
        assert slides == {f"ppt/slides/slide{number}.xml" for number in range(1, 12)}
        dimensions = ElementTree.fromstring(archive.read("ppt/presentation.xml")).find(
            "p:sldSz", NS
        )
        assert dimensions is not None
        assert int(dimensions.attrib["cx"]) * 9 == int(dimensions.attrib["cy"]) * 16
        for name in names:
            if name.endswith((".xml", ".rels")):
                document = ElementTree.fromstring(archive.read(name))
                if name.endswith(".rels"):
                    for relation in document:
                        assert relation.get("TargetMode") != "External"
                        directory = posixpath.dirname(posixpath.dirname(name))
                        target = posixpath.normpath(
                            posixpath.join(directory, relation.attrib["Target"])
                        ).lstrip("/")
                        assert target in names, (name, target)


def test_projector_body_text_is_at_least_twenty_points() -> None:
    with zipfile.ZipFile(DECK) as archive:
        for number in range(1, 12):
            document = ElementTree.fromstring(archive.read(f"ppt/slides/slide{number}.xml"))
            body_shapes = 0
            for shape in document.findall(".//p:sp", NS):
                identity = shape.find("p:nvSpPr/p:cNvPr", NS)
                assert identity is not None
                if not identity.attrib["name"].startswith("body-text-"):
                    continue
                body_shapes += 1
                for paragraph in shape.findall("p:txBody/a:p", NS):
                    style = paragraph.find("a:pPr/a:defRPr", NS)
                    assert style is not None
                    assert int(style.attrib["sz"]) >= 2000, (number, identity.attrib["name"])
            assert body_shapes >= 3


def test_trend_chart_displays_actual_committed_metrics() -> None:
    with zipfile.ZipFile(DECK) as archive:
        slide = ElementTree.fromstring(archive.read("ppt/slides/slide6.xml"))
    labels = {element.text for element in slide.findall(".//a:t", NS)}
    with (ROOT / "research/etf_trend/results/metrics.csv").open(newline="") as handle:
        rows = {
            row["model"]: row
            for row in csv.DictReader(handle)
            if row["defense"] == "BIL" and row["one_way_cost_bps"] == "20"
        }
    for model in ("SPY", "STATIC80", "STATIC70", "ABS12", "SMA10"):
        for metric in ("cagr", "max_drawdown"):
            assert f"{float(rows[model][metric]) * 100:.2f}%" in labels
    assert "REAL RESEARCH · EXPLORATORY / NAV-BASED" in labels
    assert "NOT PRODUCTION-READY" in labels
    assert "NAV proxy, not executable closes." in labels


def test_complete_script_notes_and_six_minute_forty_second_timing() -> None:
    raw = (DEMO / "presentation-script.md").read_text()
    sections = re.findall(
        r"^## Slide (\d+) — [^\n]+\n(.*?)(?=^## Slide |^## Source and scope|\Z)",
        raw,
        re.M | re.S,
    )
    assert [number for number, _ in sections] == [str(number) for number in range(1, 12)]
    seconds = 0
    with zipfile.ZipFile(DECK) as archive:
        for number, body in sections:
            timing = re.search(r"\*\*Timing:\*\* (\d+) seconds", body)
            assert timing is not None
            duration = int(timing[1])
            seconds += duration
            document = ElementTree.fromstring(
                archive.read(f"ppt/notesSlides/notesSlide{number}.xml")
            )
            notes = "\n".join(
                "".join(element.text or "" for element in paragraph.findall(".//a:t", NS))
                for paragraph in document.findall(".//a:p", NS)
            )
            for heading in ("Goal", "Script", "Transition"):
                assert f"### {heading}" in notes
            assert body.strip() in notes
            parts = re.findall(r"^### (Script|Transition)\n(.*?)(?=^### |\Z)", body, re.M | re.S)
            spoken = " ".join(
                text for heading, text in parts if heading == "Script" or number != "11"
            )
            words = len(re.findall(r"\b[\w]+(?:['’-][\w]+)*\b", spoken))
            speech_seconds = duration - (45 if number == "7" else 0)
            assert words * 60 / speech_seconds <= 155
    assert seconds == 400


def test_validation_report_is_bound_to_the_deck_and_research() -> None:
    report = json.loads((DEMO / "assets/deck-validation.json").read_text())
    assert report["sha256"] == hashlib.sha256(DECK.read_bytes()).hexdigest()
    assert report["slides"] == 11
    assert report["presentation_seconds"] == 400
    metrics = ROOT / "research/etf_trend/results/metrics.csv"
    assert report["metric_source_sha256"] == hashlib.sha256(metrics.read_bytes()).hexdigest()


def test_rendered_fallbacks_match_the_deck_validation_receipt() -> None:
    report = json.loads((DEMO / "assets/deck-validation.json").read_text())
    rendering = report["rendering"]
    assert isinstance(rendering, dict), "Refresh derived artifacts with generate_slides.py --render"
    assert rendering["rendered_pages"] == 11
    pdf = (DEMO / "Agentic-Quant-Lab-Demo.pdf").read_bytes()
    assert pdf.startswith(b"%PDF-")
    assert rendering["pdf_sha256"] == hashlib.sha256(pdf).hexdigest()
    preview = (DEMO / "assets/deck-preview.png").read_bytes()
    assert rendering["preview_sha256"] == hashlib.sha256(preview).hexdigest()
    for number in range(1, 12):
        name = f"slide-{number:02}.png"
        png = (DEMO / "assets/slides" / name).read_bytes()
        assert png[:8] == b"\x89PNG\r\n\x1a\n"
        width, height = struct.unpack(">II", png[16:24])
        assert width * 9 == height * 16
        assert width >= 1280
        assert rendering["slide_image_sha256"][name] == hashlib.sha256(png).hexdigest()


def test_fallback_transcript_and_receipt_are_consistent_and_synthetic() -> None:
    transcript = (DEMO / "demo-output.txt").read_text()
    assert transcript == (DEMO / "assets/offline-demo/terminal.txt").read_text()
    assert (
        "MODE: DEMO | DATA: SYNTHETIC FIXTURE | LIVE TRADING: DISABLED | EXECUTION: DRY RUN"
        in transcript
    )
    assert "/home/runner/" not in transcript
    receipt = json.loads((DEMO / "assets/offline-demo/receipt.json").read_text())
    assert receipt["mode"] == "demo"
    assert receipt["execution"] == "dry_run"
    assert receipt["live_trading"] == "DISABLED"
    assert receipt["data"].startswith("SYNTHETIC")
    for key in ("experiment_hash", "input_hash", "strategy_config_hash", "result_hash"):
        assert re.fullmatch(r"[0-9a-f]{64}", receipt[key])
        assert f"{key}: {receipt[key]}" in transcript
    result = json.loads((DEMO / "assets/offline-demo/result.json").read_text())
    assert result["configuration"]["risk_policy"]["live_execution_enabled"] is False


def test_risk_slide_matches_the_captured_demo_order() -> None:
    transcript = (DEMO / "demo-output.txt").read_text()
    order = re.search(r"Would submit: (BUY) (\d+) shares ([A-Z0-9_.-]+)", transcript)
    notional = re.search(r"Estimated notional: \$(\d[\d,]*\.\d{2})", transcript)
    assert order is not None and notional is not None
    with zipfile.ZipFile(DECK) as archive:
        slide = ElementTree.fromstring(archive.read("ppt/slides/slide8.xml"))
    labels = {element.text for element in slide.findall(".//a:t", NS)}
    assert f"{order[1]} {order[2]}" in labels
    assert order[3] in labels
    assert f"≈ ${notional[1]}" in labels


def test_runbook_uses_the_published_branch_and_portable_paths() -> None:
    runbook = (DEMO / "demo-runbook.md").read_text()
    assert "git checkout demo/final-presentation" in runbook
    assert "uv sync\nuv run aql demo --reset\nuv run aql demo" in runbook
    assert "uv run --offline --no-sync aql demo" in runbook
    assert "cat demo/demo-output.txt" in runbook
    assert "/home/runner/" not in runbook
    assert "This is not a live result." in " ".join(runbook.split())
