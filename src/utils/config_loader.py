"""Loads config/config.yaml (and .env) into a single dict used across modules."""

import os
import yaml
from dotenv import load_dotenv

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "config", "config.yaml")


def load_config(path: str = CONFIG_PATH) -> dict:
    load_dotenv()  # populate os.environ from .env
    with open(path, "r") as f:
        config = yaml.safe_load(f)
    return config
