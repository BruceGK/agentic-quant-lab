from pathlib import Path
from unittest.mock import patch

import pytest

from agentic_quant_lab.azure_auth import POSTGRES_SCOPE, azure_credential
from agentic_quant_lab.config import BlobSettings, Settings
from agentic_quant_lab.database import connect_database

AZURE_DSN = (
    "host=aqltest.postgres.database.azure.com dbname=aql user=aql_recorder "
    "sslmode=verify-full sslrootcert=/etc/ssl/certs/ca-certificates.crt"
)


def test_local_azure_credentials_require_explicit_subscription(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("IDENTITY_ENDPOINT", raising=False)
    monkeypatch.setenv("AZURE_SUBSCRIPTION_ID", "synthetic-subscription")
    with patch("agentic_quant_lab.azure_auth.AzureCliCredential") as credential:
        assert azure_credential() is credential.return_value
        credential.assert_called_once_with(
            subscription="synthetic-subscription", process_timeout=30
        )
    monkeypatch.delenv("AZURE_SUBSCRIPTION_ID")
    with pytest.raises(KeyError):
        azure_credential()


def test_container_uses_only_explicit_runtime_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("IDENTITY_ENDPOINT", "http://localhost/synthetic-identity")
    monkeypatch.setenv("AZURE_CLIENT_ID", "synthetic-client-id")
    with (
        patch("agentic_quant_lab.azure_auth.ManagedIdentityCredential") as managed,
        patch("agentic_quant_lab.azure_auth.AzureCliCredential") as cli,
    ):
        assert azure_credential() is managed.return_value
        managed.assert_called_once_with(client_id="synthetic-client-id")
        cli.assert_not_called()
    monkeypatch.delenv("AZURE_CLIENT_ID")
    with pytest.raises(KeyError):
        azure_credential()


def test_azure_postgres_uses_ephemeral_token_not_dsn_password(tmp_path: Path) -> None:
    settings = Settings(AZURE_DSN, tmp_path / "unused", "", database_auth="azure")
    with (
        patch("agentic_quant_lab.database.azure_credential") as credential,
        patch("agentic_quant_lab.database.psycopg.connect") as connect,
    ):
        entered = credential.return_value.__enter__.return_value
        entered.get_token.return_value.token = "synthetic-short-lived-token"
        assert connect_database(settings) is connect.return_value
        entered.get_token.assert_called_once_with(POSTGRES_SCOPE)
        connect.assert_called_once_with(
            AZURE_DSN, password="synthetic-short-lived-token", autocommit=True, connect_timeout=15
        )
    assert "synthetic-short-lived-token" not in repr(settings)


@pytest.mark.parametrize(
    "dsn",
    [
        AZURE_DSN.replace("verify-full", "require"),
        AZURE_DSN.replace("aqltest.postgres.database.azure.com", "attacker.example.invalid"),
        AZURE_DSN + " password=synthetic-password",
        "dbname=aql user=aql_recorder",
    ],
)
def test_azure_postgres_rejects_unverified_or_credentialed_destinations(
    dsn: str, tmp_path: Path
) -> None:
    with (
        patch("agentic_quant_lab.database.azure_credential") as credential,
        pytest.raises(ValueError),
    ):
        connect_database(Settings(dsn, tmp_path / "unused", "", database_auth="azure"))
    credential.assert_not_called()


def test_password_authentication_preserves_local_behavior(tmp_path: Path) -> None:
    settings = Settings("postgresql:///unused", tmp_path / "unused", "")
    with patch("agentic_quant_lab.database.psycopg.connect") as connect:
        connect_database(settings)
    connect.assert_called_once_with(settings.database_url, autocommit=True)


@pytest.mark.parametrize(
    "url",
    [
        "http://aqltest.blob.core.windows.net",
        "https://aqltest.blob.core.windows.net?sig=synthetic",
        "https://secret@aqltest.blob.core.windows.net",
        "https://attacker.example.invalid",
        "https://aqltest.blob.core.windows.net/container",
    ],
)
def test_blob_account_url_cannot_contain_credentials_or_foreign_host(url: str) -> None:
    with pytest.raises(ValueError):
        BlobSettings(url)


@pytest.mark.parametrize(
    "container,prefix", [("Bad", "sec"), ("bad--name", "sec"), ("valid", "../")]
)
def test_blob_namespace_validation(container: str, prefix: str) -> None:
    with pytest.raises(ValueError):
        BlobSettings("https://aqltest.blob.core.windows.net", container, prefix)


def test_unknown_backend_and_database_auth_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql:///unused")
    monkeypatch.setenv("LEDGER_BACKEND", "azuer")
    with pytest.raises(ValueError, match="LEDGER_BACKEND"):
        Settings.from_env(require_sec=False)
    monkeypatch.setenv("LEDGER_BACKEND", "local")
    monkeypatch.setenv("DATABASE_AUTH", "azuer")
    with pytest.raises(ValueError, match="DATABASE_AUTH"):
        Settings.from_env(require_sec=False)
