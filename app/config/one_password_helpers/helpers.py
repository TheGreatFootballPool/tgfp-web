""" Helpers for Prefect """
import os
from onepassword.client import Client


# pylint: disable=too-few-public-methods
class OnePasswordHelper:
    """ Helper class for 1Password """
    def __init__(self, environment: str):
        self._env: str = environment

    async def get_setting(self, secret_name: str) -> str:
        """ Retrieves the secret, using the current environment """
        token = os.getenv("OP_SERVICE_ACCOUNT_TOKEN")
        client = await Client.authenticate(auth=token, integration_name="My 1Password Integration",
                                           integration_version="v1.0.0")
        value = await client.secrets.resolve(f"op://secrets/TGFP/{self._env}/{secret_name}")
        return value
