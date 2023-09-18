""" Helpers for Prefect """
import os

from prefect import variables
from prefect.blocks.system import Secret


def get_secret(secret_name: str, is_var: bool = False, use_env: bool = True) -> str:
    """ Retrieves the secret or variable, using the current environment """
    env: str = os.getenv('ENVIRONMENT')
    env_string: str = f"-{env}" if use_env else ""
    if is_var:
        env_string: str = f"_{env}" if use_env else ""
        return str(variables.get(f"{secret_name}{env_string}"))
    return Secret.load(f"{secret_name}{env_string}").get()
