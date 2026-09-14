import os

from azure.identity import AzureCliCredential, ManagedIdentityCredential

POSTGRES_SCOPE = "https://ossrdbms-aad.database.windows.net/.default"


def azure_credential() -> AzureCliCredential | ManagedIdentityCredential:
    if os.getenv("IDENTITY_ENDPOINT"):
        return ManagedIdentityCredential(client_id=os.environ["AZURE_CLIENT_ID"])
    return AzureCliCredential(subscription=os.environ["AZURE_SUBSCRIPTION_ID"], process_timeout=30)
