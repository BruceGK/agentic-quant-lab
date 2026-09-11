import json
import ssl
import subprocess
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from unittest.mock import MagicMock, patch
from urllib.request import HTTPSHandler, build_opener

import pytest

from agentic_quant_lab.cli import main
from agentic_quant_lab.config import Settings
from agentic_quant_lab.ledger import LedgerError
from agentic_quant_lab.sec import NoRedirect


@pytest.fixture
def receiver(tmp_path: Path) -> Iterator[tuple[str, ssl.SSLContext, list[dict], list[int]]]:
    key, cert = tmp_path / "key.pem", tmp_path / "cert.pem"
    subprocess.run(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-subj",
            "/CN=localhost",
            "-addext",
            "subjectAltName=DNS:localhost",
            "-days",
            "1",
            "-keyout",
            str(key),
            "-out",
            str(cert),
        ],
        check=True,
        capture_output=True,
    )
    received: list[dict] = []
    response_status = [204]

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            received.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            self.send_response(response_status[0])
            if response_status[0] == 302:
                self.send_header("Location", "/must-not-follow")
            self.end_headers()

        def log_message(self, format: str, *args: object) -> None:
            pass

    server = ThreadingHTTPServer(("localhost", 0), Handler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(cert, key)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield (
            f"https://localhost:{server.server_port}/synthetic-hook",
            ssl.create_default_context(cafile=str(cert)),
            received,
            response_status,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.mark.parametrize("status", [204, 302, 500])
def test_real_local_https_heartbeat_acknowledgement(
    receiver: tuple[str, ssl.SSLContext, list[dict], list[int]],
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    status: int,
) -> None:
    url, context, received, response_status = receiver
    response_status[0] = status
    settings = Settings("postgresql:///unused", tmp_path / "ledger", "", heartbeat_url=url)
    recorder = MagicMock()
    recorder.__enter__.return_value = recorder
    recorder.record.return_value = 1
    recorder.ledger.records = [{"sequence": 2, "hash": "a" * 64}]
    with (
        patch("sys.argv", ["quant-recorder", "record"]),
        patch("agentic_quant_lab.cli.Settings.from_env", return_value=settings),
        patch("agentic_quant_lab.cli.Recorder", return_value=recorder),
        patch(
            "agentic_quant_lab.cli.build_opener",
            return_value=build_opener(HTTPSHandler(context=context), NoRedirect()),
        ),
    ):
        if status == 204:
            main()
            assert json.loads(capsys.readouterr().out)["heartbeat"] == "sent"
        else:
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 1
            assert json.loads(capsys.readouterr().err)["status"] == "failed"
    assert received == [{"status": "success", "new_filings": 1, "sequence": 2, "hash": "a" * 64}]
    recorder.reconcile.assert_called_once()


def test_divergence_prevents_healthy_heartbeat(tmp_path: Path) -> None:
    recorder = MagicMock()
    recorder.__enter__.return_value = recorder
    recorder.record.return_value = 0
    recorder.reconcile.side_effect = LedgerError("divergence")
    settings = Settings("", tmp_path / "ledger", "", heartbeat_url="https://example.invalid/hook")
    with (
        patch("sys.argv", ["quant-recorder", "record"]),
        patch("agentic_quant_lab.cli.Settings.from_env", return_value=settings),
        patch("agentic_quant_lab.cli.Recorder", return_value=recorder),
        patch("agentic_quant_lab.cli.build_opener") as opener,
        pytest.raises(SystemExit),
    ):
        main()
    opener.assert_not_called()


def test_missing_heartbeat_is_explicit(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    settings = Settings("", tmp_path / "ledger", "")
    recorder = MagicMock()
    recorder.__enter__.return_value = recorder
    recorder.record.return_value = 0
    recorder.ledger.records = []
    with (
        patch("sys.argv", ["quant-recorder", "record"]),
        patch("agentic_quant_lab.cli.Settings.from_env", return_value=settings),
        patch("agentic_quant_lab.cli.Recorder", return_value=recorder),
    ):
        main()
    assert json.loads(capsys.readouterr().out)["heartbeat"] == "disabled"


def test_cli_never_prints_libpq_password_fragments(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    password = "SYNTHETIC_password_50%done"
    settings = Settings(f"postgresql://user:{password}@localhost/db", tmp_path / "ledger", "")
    with (
        patch("sys.argv", ["quant-recorder", "replay"]),
        patch("agentic_quant_lab.cli.Settings.from_env", return_value=settings),
        pytest.raises(SystemExit),
    ):
        main()
    output = capsys.readouterr()
    assert password not in output.err + output.out
    assert "postgresql" not in output.err + output.out
    assert json.loads(output.err) == {"status": "failed", "error": "recorder_failed"}


def test_cli_never_prints_invalid_hook_path(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    token = "synthetic-sensitive-hook"
    settings = Settings("", tmp_path / "ledger", "", heartbeat_url=f"https://localhost/{token} x")
    recorder = MagicMock()
    recorder.__enter__.return_value = recorder
    recorder.record.return_value = 0
    recorder.ledger.records = []
    with (
        patch("sys.argv", ["quant-recorder", "record"]),
        patch("agentic_quant_lab.cli.Settings.from_env", return_value=settings),
        patch("agentic_quant_lab.cli.Recorder", return_value=recorder),
        pytest.raises(SystemExit),
    ):
        main()
    output = capsys.readouterr()
    assert token not in output.err + output.out
    assert json.loads(output.err)["status"] == "failed"
