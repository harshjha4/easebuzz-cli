import typer
from rich.table import Table

from config.config import init_config, console, display_diagnostic_curl
from services.payment_status import transaction_status_logic

payments_status_app = typer.Typer(help="Execute status api for transaction status check.")


@payments_status_app.command("check")
def payment_status(
        # --- Mandatory Fields ---
        txnid: str = typer.Option(..., "--txnid", "-t", prompt="Enter Transaction ID (txnid)"),
        amount: float = typer.Option(..., "--amount", "-a", prompt="Enter Transaction Amount"),
        email: str = typer.Option(..., "--email", "-e", prompt="Enter Customer Email"),
        phone: str = typer.Option(..., "--phone", "-p", prompt="Enter Customer Phone"),

        # --- Config Overrides ---
        key: str = typer.Option(None, "--key", help="Override Merchant Key for this execution"),
        salt: str = typer.Option(None, "--salt",
                                       help="Override Merchant Salt/Secret for this execution"),
        env: str = typer.Option(None, "--env", help="Override Target Environment (sandbox/dev/production)")
):
    """Query the Easebuzz database for the exact status of a specific transaction."""
    config = init_config()

    # Apply CLI config overrides if provided
    if key: config["key"] = key
    if salt: config["salt"] = salt
    if env: config["env"] = env.lower()

    if not config.get("key") or not config.get("salt"):
        console.print("[bold red]CLI unconfigured. Pass --key and --secret, or run 'easebuzz configure'.[/bold red]")
        raise typer.Exit(1)

    current_env = config.get("env", "sandbox")

    with console.status(f"[bold cyan] Querying Easebuzz {current_env.upper()} database for '{txnid}'..."):
        payload, endpoint_url, res_data = transaction_status_logic(config, txnid, amount, email, phone)

    display_diagnostic_curl(endpoint_url, payload)

    # Check for successful payload parsing
    if res_data.get("status") is True and "msg" in res_data:
        msg_data = res_data["msg"]
        gateway_status = msg_data.get("status", "Unknown")

        # Color routing for terminal aesthetics
        if gateway_status.lower() == "success":
            color = "green"
        elif gateway_status.lower() in ["usercancelled", "failure", "bounced"]:
            color = "red"
        else:
            color = "yellow"

        console.print(f"\n[bold {color}]Transaction Found: {gateway_status.upper()}[/bold {color}]")

        table = Table(title="Transaction Database Record")
        table.add_column("Parameter", style="cyan")
        table.add_column("Value", style="white")

        # Extracting key fields from the Easebuzz response object
        table.add_row("Transaction ID (txnid)", msg_data.get("txnid", txnid))
        table.add_row("Easebuzz PG ID", msg_data.get("easepayid", "N/A"))
        table.add_row("Amount Captured", f"INR {msg_data.get('amount', amount)}")
        table.add_row("Deduction (Net)", f"INR {msg_data.get('net_amount_debit', '0.00')}")
        table.add_row("Mode / Bankcode", f"{msg_data.get('mode', 'N/A')} - {msg_data.get('bankcode', 'N/A')}")
        table.add_row("Timestamp", msg_data.get("addedon", "N/A"))
        table.add_row("Error Message", msg_data.get("error_Message", "None"))

        console.print(table)
    else:
        console.print(f"\n[bold red] Failed to retrieve transaction status:[/bold red]")
        console.print_json(data=res_data)