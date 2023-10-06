""" Small script to load prefect secrets """
import os
import sys
from pathlib import Path

import dotenv
from prefect.blocks.system import Secret
from dotenv import load_dotenv

load_dotenv(Path('stack.env'))
if __name__ == '__main__':
    SECRET = sys.argv[1]
    assert os.getenv('PREFECT_API_KEY')
    print(Secret.load(f"{SECRET}").get())
    dotenv.set_key(Path('stack.env'), "key", "value")
