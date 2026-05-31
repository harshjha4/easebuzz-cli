# config/config.py
import hashlib
import os
import secrets
import string

import typer
from rich.console import Console
from dynaconf import Dynaconf
import sys
import json
from pathlib import Path

CONFIG_DIR  = ".easebuzz"
CONFIG_FILE = "config"
CONFIG_TYPE = "json"
DEFAULT_OUTPUT_FORMAT = "json"

ENV_URLS = {
    "sandbox": "https://testpay.easebuzz.in/payment/initiateLink",
    "production": "https://pay.easebuzz.in/payment/initiateLink"
}

app = typer.Typer(help="Easebuzz CLI tool for testing merchant integrations.")
console = Console()

def home_path(exit_sys=True):
    try:
        return Path.home()
    except Exception as e:
        console.print(f"[bold red]Error resolving user home directory:[/bold red] {e}", file=sys.stderr)
        if exit_sys:
            sys.exit(1)
        raise e

def config_file_path():
    return home_path() / CONFIG_DIR / f"{CONFIG_FILE}.{CONFIG_TYPE}"


def init_config():
    cfg_path = config_file_path()
    settings = Dynaconf(
        settings_files=[str(cfg_path)],
        envvar_prefix="EASEBUZZ",
        load_dotenv=True,
        default_settings={
            "OUTPUT_FORMAT": DEFAULT_OUTPUT_FORMAT
        }
    )

    return settings


def save(key: str, salt: str, env: str):
    home = home_path(exit_sys=False)
    config_dir_path = home / CONFIG_DIR

    config_dir_path.mkdir(mode=0o700, parents=True, exist_ok=True)

    config_data = {
        "key": key,
        "salt": salt,
        "env": env
    }

    file_path = config_dir_path / f"{CONFIG_FILE}.{CONFIG_TYPE}"
    with open(file_path, "w") as f:
        json.dump(config_data, f, indent=4)

def generate_txnid(length=12):
    chars = string.ascii_letters + string.digits
    return "TXN" + "".join(secrets.choice(chars) for _ in range(length))

def generate_hash(data, salt):
    hash_sequence = (
        f"{data['key']}|{data['txnid']}|{data['amount']}|{data['productinfo']}|"
        f"{data['firstname']}|{data['email']}|||||||||||{salt}"
    )
    return hashlib.sha512(hash_sequence.encode('utf-8')).hexdigest().lower()