import hashlib
import secrets
import string
from typing import Any

import requests
import typer
from rich.console import Console
from dynaconf import Dynaconf
import sys
import json
from pathlib import Path

from rich.panel import Panel
from rich.prompt import Confirm, Prompt

CONFIG_DIR  = ".easebuzz"
CONFIG_FILE = "config"
CONFIG_TYPE = "json"
DEFAULT_OUTPUT_FORMAT = "json"

ENV_URLS = {
    "dev": {
        "initiate": "https://pay.easebuzz.dev/payment/initiateLink",
        "seamless": "https://pay.easebuzz.dev/initiate_seamless_payment/",
        "status": "https://dashboard.easebuzz.dev/transaction/v1/retrieve"
    },
    "sandbox": {
        "initiate": "https://testpay.easebuzz.in/payment/initiateLink",
        "seamless": "https://testpay.easebuzz.in/initiate_seamless_payment/",
        "status": "https://testdashboard.easebuzz.in/transaction/v1/retrieve"
    },
    "production": {
        "initiate": "https://pay.easebuzz.in/payment/initiateLink",
        "seamless": "https://pay.easebuzz.in/initiate_seamless_payment/",
        "status": "https://dashboard.easebuzz.in/transaction/v1/retrieve"
    }
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

def get_active_endpoint(work: str, path: str) -> str:
    """
    Constructs the absolute URL based on the user's configured environment.
    """
    config = init_config()
    current_env = config.get("env", "sandbox")

    # Fallback to sandbox if environment is unmapped
    base_domain = ENV_URLS.get(current_env, ENV_URLS["sandbox"]).get(work)
    if not base_domain:
        print("[bold red] Failed to initiate Payment, no url found")
        sys.exit(1)
    return f"{base_domain}{path}"


def display_diagnostic_curl(url: str, payload: dict):
    """
    Renders an exact copy-pasteable curl string containing fully compiled
    hashes and structural variables. Used by merchants to debug payload issues.
    """
    curl_body = " \\\n".join([f"  -d '{k}={v}'" for k, v in payload.items()])
    curl_command = (
        f"curl -X POST '{url}' \\\n"
        f"  -H 'Content-Type: application/x-www-form-urlencoded' \\\n"
        f"  -H 'Accept: application/json' \\\n"
        f"{curl_body}"
    )
    console.print(
        Panel(
            curl_command,
            title="[bold green] Merchant Diagnostic cURL (Copy/Paste to Validate Integration)[/bold green]",
            border_style="green",
            expand=False
        )
    )

def post_execute_single_payload(endpoint_url: str, payload: dict) -> dict:
    """Executes an isolated form-encoded POST transaction against Easebuzz servers."""
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    try:
        response = requests.post(endpoint_url, data=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json()
        return {"status": 0, "error": f"HTTP Gateway Error Code: {response.status_code}"}
    except requests.RequestException as e:
        return {"status": 0, "error": str(e)}


# def collect_dynamic_args(ctx: typer.Context, interactive: bool, schema: Any) -> dict:
#     """Helper to collect optional terminal arguments and interactive wizard inputs."""
#     extra_args = {}
#
#     # Parse CLI Flags
#     if ctx.args:
#         for i in range(0, len(ctx.args), 2):
#             flag = ctx.args[i].lstrip("-")
#             if flag in schema:
#                 val = ctx.args[i + 1] if i + 1 < len(ctx.args) else ""
#                 extra_args[flag] = val
#
#     # Interactive Wizard
#     if interactive:
#         console.print("\n[bold yellow]Optional Fields Wizard:[/bold yellow]")
#         for field_key, prompt_text in schema.items():
#             if field_key in extra_args:
#                 continue
#             if Confirm.ask(f"Add [cyan]{field_key}[/cyan] ({prompt_text})?", default=False):
#                 extra_args[field_key] = Prompt.ask(f"Enter [cyan]{field_key}[/cyan]")
#
#     return extra_args


# def collect_dynamic_args(interactive: bool, schema: Any, current_args: dict) -> dict:
#     """Helper to launch a step-by-step wizard for optional fields."""
#     if not interactive:
#         return current_args
#
#     console.print("\n[bold yellow]Optional Fields Wizard:[/bold yellow]")
#     for field_key, prompt_text in schema.items():
#         # Skip asking if the user already passed it as a CLI flag (e.g., --udf1)
#         if field_key in current_args:
#             continue
#
#         if Confirm.ask(f"Add [cyan]{field_key}[/cyan] ({prompt_text})?", default=False):
#             current_args[field_key] = Prompt.ask(f"Enter [cyan]{field_key}[/cyan]")
#
#     return current_args

def collect_dynamic_args(
        interactive: bool,
        schema: dict,
        current_args: dict,
        ask_confirm: bool = True
) -> dict:
    """
    Unified wizard to collect inputs dynamically from a metadata schema.

    :param interactive: If False, skips processing and returns current_args immediately.
    :param schema: The schema dictionary containing field metadata.
    :param current_args: Existing arguments (passed via CLI flags) to skip.
    :param ask_confirm: If True, asks 'Add [field]?' before prompting. If False, prompts directly.
    """
    if not interactive:
        return current_args

    for field_key, meta in schema.items():
        # Skip if already provided via CLI flags/overrides
        if field_key in current_args:
            continue

        label = meta.get("label", field_key)
        field_type = meta.get("type", str)
        is_secret = "cvv" in field_key.lower()

        # Step 1: Handle confirmation gate if required
        should_prompt = True
        if ask_confirm:
            should_prompt = Confirm.ask(f"Add [cyan]{field_key}[/cyan] ({label})?", default=False)

        # Step 2: Collect input based on field type
        if should_prompt:
            if field_type == bool:
                current_args[field_key] = Confirm.ask(f"  [magenta]>[/magenta] {label}")
            else:
                user_input = Prompt.ask(f"  [magenta]>[/magenta] {label}", password=is_secret)
                # Only add string values if the user actually typed something
                if user_input:
                    current_args[field_key] = user_input

    return current_args