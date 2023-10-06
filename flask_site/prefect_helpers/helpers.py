""" Helpers for Prefect """
import os

from prefect import variables
from prefect.blocks.system import Secret


class PrefectHelper:
    """ Helper class for Prefect """
    def __init__(self, environment: str):
        self._env: str = environment

    def get_secret(self, secret_name: str) -> str:
        """ Retrieves the secret, using the current environment """
        assert os.getenv('PREFECT_API_KEY')
        assert os.getenv('PREFECT_API_URL')
        return Secret.load(f"{secret_name}-{self._env}").get()

    def get_variable(self, variable_name: str) -> str:
        """ Retrieves the variable, using the current environment """
        return str(variables.get(f"{variable_name}_{self._env}"))
