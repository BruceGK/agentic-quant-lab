from collections.abc import Iterator
from typing import Any, Self

from azure.core.exceptions import ResourceExistsError
from azure.identity import AzureCliCredential, ManagedIdentityCredential
from azure.storage.blob import ContainerClient, ContentSettings

from agentic_quant_lab.azure_auth import azure_credential
from agentic_quant_lab.config import BlobSettings
from agentic_quant_lab.ledger import LedgerError, canonical, make_record, verify_lines


class BlobLedger:
    """One atomically created block blob per canonical JSONL record; never overwrites."""

    def __init__(self, settings: BlobSettings):
        self.settings = settings
        self.records: list[dict[str, Any]] = []
        self._client: ContainerClient | None = None
        self._credential: AzureCliCredential | ManagedIdentityCredential | None = None
        self._failed = False

    def __enter__(self) -> Self:
        try:
            self._credential = azure_credential()
            self._client = ContainerClient(
                self.settings.account_url,
                self.settings.container,
                credential=self._credential,
                connection_timeout=10,
                read_timeout=60,
                retry_total=3,
            )
            self.records = self.read_records()
            self._failed = False
        except BaseException:
            self.__exit__()
            raise
        return self

    def __exit__(self, *_: Any) -> None:
        try:
            if self._client is not None:
                self._client.close()
        finally:
            self._client = None
            if self._credential is not None:
                self._credential.close()
                self._credential = None

    def _name(self, sequence: int) -> str:
        return f"{self.settings.prefix}/records/{sequence:020d}.jsonl"

    def read_records(self) -> list[dict[str, Any]]:
        if self._client is None:
            raise LedgerError("Blob ledger is closed")
        client = self._client
        names = sorted(
            blob.name
            for blob in client.list_blobs(name_starts_with=f"{self.settings.prefix}/records/")
        )

        def lines() -> Iterator[bytes]:
            for sequence, name in enumerate(names, 1):
                if name != self._name(sequence):
                    raise LedgerError("Blob ledger has missing or unexpected record names")
                yield client.download_blob(name).readall()

        return verify_lines(lines())

    def append(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        if self._client is None or self._failed:
            raise LedgerError("Blob ledger is closed or a prior write failed; reopen and verify")
        record = make_record(self.records, kind, payload)
        try:
            # A conditional block-blob commit supports large SEC records and prevents
            # concurrent writers (even with different databases) from forking a sequence.
            self._client.upload_blob(
                self._name(record["sequence"]),
                canonical(record) + b"\n",
                overwrite=False,
                content_settings=ContentSettings(content_type="application/x-ndjson"),
            )
        except ResourceExistsError as exc:
            self._failed = True
            raise LedgerError("Blob ledger sequence already exists; reopen and verify") from exc
        except BaseException:
            self._failed = True
            raise
        self.records.append(record)
        return record
