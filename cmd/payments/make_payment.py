import concurrent.futures
import random
import secrets
import requests
import typer
from rich.panel import Panel
from rich.table import Table

from config.config import console, init_config, ENV_URLS, generate_txnid, generate_hash

payments_app = typer.Typer(help="Execute manual, targeted mode, and asynchronous bulk payment simulations.")


def get_active_endpoint(path: str = "/payment/initiateLink") -> str:
    """
    Constructs the absolute URL based on the user's configured environment.
    """
    config = init_config()
    current_env = config.get("env", "sandbox")

    # Fallback to sandbox if environment is unmapped
    base_domain = ENV_URLS.get(current_env, ENV_URLS["sandbox"])
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
            title="[bold green]📋 Merchant Diagnostic cURL (Copy/Paste to Validate Integration)[/bold green]",
            border_style="green",
            expand=False
        )
    )


def execute_single_payload(endpoint_url: str, payload: dict) -> dict:
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


@payments_app.command("initiate")
def initiate_payment(
        amount: float = typer.Option(..., prompt="Enter payment amount (e.g., 50.00)"),
        name: str = typer.Option(..., prompt="Customer First Name"),
        email: str = typer.Option(..., prompt="Customer Email ID"),
        phone: str = typer.Option(..., prompt="Customer Mobile Number"),
        product: str = typer.Option("CLI_Purchase", prompt="Product Info/Description"),
        mode: str = typer.Option("ALL", "--mode", "-m", help="Restrict payment methods: NB, CC, DC, UPI, or ALL")
):
    """Generate and dispatch a new payment transaction link to Easebuzz."""
    config = init_config()

    # Ensure CLI is configured
    if not config.get("key") or not config.get("salt"):
        console.print("[bold red]Error: CLI not configured. Run 'easebuzz configure' first.[/bold red]")
        raise typer.Exit(code=1)

    current_env = config.get("env", "sandbox")
    endpoint_url = get_active_endpoint("/payment/initiateLink")
    txnid = generate_txnid()

    payload = {
        "key": config.get("key"),
        "txnid": txnid,
        "amount": f"{amount:.2f}",
        "firstname": name,
        "email": email,
        "phone": phone,
        "productinfo": product,
        "surl": "https://localhost/success",
        "furl": "https://localhost/failure"
    }

    # Bind explicit execution routing options if selected by testing agent
    if mode.upper() != "ALL":
        payload["payment_mode"] = mode.upper()

    # Compute hash signature utilizing imported utilities
    with console.status("[bold blue]Calculating cryptographic validation signatures..."):
        payload["hash"] = generate_hash(payload, config.get("salt"))

    # Output the exact curl block for merchant copy-pasting
    display_diagnostic_curl(endpoint_url, payload)

    with console.status(f"[bold magenta]Contacting Easebuzz {current_env.upper()} servers..."):
        res_data = execute_single_payload(endpoint_url, payload)

        if res_data.get("status") == 1:
            console.print("\n[bold green]✅ Transaction initiated successfully![/bold green]")
            table = Table(title=f"Transaction Summary ({current_env.upper()})")
            table.add_column("Parameter", style="cyan")
            table.add_column("Value", style="magenta")
            table.add_row("Transaction ID", txnid)
            table.add_row("Amount", f"INR {amount:.2f}")
            table.add_row("Customer", name)
            if "payment_mode" in payload:
                table.add_row("Enforced Mode", payload["payment_mode"])

            console.print(table)
            console.print(Panel(
                f"[bold cyan] Payment Link / Access Key Reference:[/bold cyan]\n{res_data.get('data')}",
                title="Action Data"
            ))
        else:
            console.print(
                f"\n[bold red] Easebuzz {current_env.upper()} API error returned or connection dropped:[/bold red]")
            console.print_json(data=res_data)


@payments_app.command("bulk")
def bulk_payment(
        count: int = typer.Option(5, "--count", "-c", help="Number of distinct unique executions"),
        amount: float = typer.Option(10.00, "--amount", "-a", help="Base static fallback processing currency tier")
):
    """
    Boom! Fire off multiple randomized orders simultaneously to simulate high-load testing.
    """
    config = init_config()

    if not config.get("key") or not config.get("salt"):
        console.print("[bold red]Error: CLI not configured. Run 'easebuzz configure' first.[/bold red]")
        raise typer.Exit(code=1)

    current_env = config.get("env", "sandbox")
    endpoint_url = get_active_endpoint("/payment/initiateLink")

    console.print(
        f"[bold magenta]🚀 Dispatching {count} concurrent bulk workers against {current_env.upper()} endpoint...[/bold magenta]\n")

    # Generate payloads dynamically before executing thread pools
    payloads_pool = []
    first_names = ["Arjun", "Neha", "Kabir", "Aanya", "Rohan", "Priya", "Vikram", "Riya"]
    products = ["SaaS_License", "Cloud_Credits", "API_Premium_Pack", "Dev_Testing_Stub"]
    modes = ["ALL", "UPI", "NB", "CC"]

    for _ in range(count):
        txnid = generate_txnid()
        mock_payload = {
            "key": config.get("key"),
            "txnid": txnid,
            "amount": f"{amount + random.randint(1, 99):.2f}",
            "firstname": random.choice(first_names),
            "email": f"bulk_{secrets.token_hex(4)}@easebuzz-test.in",
            "phone": f"9{random.randint(100000001, 999999999)}",
            "productinfo": random.choice(products),
            "surl": "https://localhost/success",
            "furl": "https://localhost/failure"
        }

        chosen_mode = random.choice(modes)
        if chosen_mode != "ALL":
            mock_payload["payment_mode"] = chosen_mode

        mock_payload["hash"] = generate_hash(mock_payload, config.get("salt"))
        payloads_pool.append(mock_payload)

    results_table = Table(title=f"Asynchronous Batch Run Summary ({current_env.upper()})")
    results_table.add_column("Worker", style="dim cyan", justify="center")
    results_table.add_column("Transaction ID", style="magenta")
    results_table.add_column("Mode", style="yellow")
    results_table.add_column("Amount", style="green")
    results_table.add_column("Gateway Diagnostic Verdict", style="bold white")

    with console.status("[bold yellow]Executing parallel workers..."):
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(count, 10)) as executor:
            futures = {
                executor.submit(execute_single_payload, endpoint_url, p): p
                for p in payloads_pool
            }

            for idx, future in enumerate(concurrent.futures.as_completed(futures), start=1):
                input_payload = futures[future]
                txnid = input_payload["txnid"]
                mode_label = input_payload.get("payment_mode", "ALL")
                amt_label = f"₹{input_payload['amount']}"

                try:
                    api_response = future.result()
                    if api_response.get("status") == 1:
                        verdict = "[green] SUCCESS (200) [/green]"
                    else:
                        error_msg = api_response.get("error") or api_response.get("data", "Validation Refused")
                        verdict = f"[red] FAILED ({error_msg})[/red]"
                except Exception as exc:
                    verdict = f"[bold red] CRASHED ({str(exc)})[/bold red]"

                results_table.add_row(f"#{idx}", txnid, mode_label, amt_label, verdict)

    console.print(results_table)