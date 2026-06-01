import concurrent.futures
import random
import secrets
import string

import typer
from rich.panel import Panel
from faker import Faker
from rich.table import Table

from config.config import console, init_config, generate_txnid, generate_hash, get_active_endpoint, \
    display_diagnostic_curl, post_execute_single_payload, collect_dynamic_args
from config.constants import PAYMENT_INITIATE_SCHEMA
from services.payments import initiate_payment_logic

payments_app = typer.Typer(help="Execute manual, targeted mode, and asynchronous bulk payment simulations.")


@payments_app.command(
    "initiate",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def initiate_payment(
        ctx: typer.Context,
        amount: float = typer.Option(..., prompt="Enter payment amount (e.g., 50.00)"),
        name: str = typer.Option(..., prompt="Customer First Name"),
        email: str = typer.Option(..., prompt="Customer Email ID"),
        phone: str = typer.Option(..., prompt="Customer Mobile Number"),
        product: str = typer.Option("CLI_Purchase", prompt="Product Info/Description"),
        mode: str = typer.Option("ALL", "--mode", "-m", help="Restrict payment methods: NB, CC, DC, UPI, or ALL"),
        interactive: bool = typer.Option(False, "--interactive", "-i", help="Launch the dynamic wizard to include optional fields.")
):
    """Generate and dispatch a new payment transaction link to Easebuzz."""
    config = init_config()

    # Ensure CLI is configured
    if not config.get("key") or not config.get("salt"):
        console.print("[bold red]CLI unconfigured. Run 'easebuzz configure' first.[/bold red]")
        raise typer.Exit(1)

    current_env = config.get("env", "sandbox")
    endpoint_url = get_active_endpoint('initiate', "/payment/initiateLink")

    payload = {
        "amount": f"{amount:.2f}",
        "firstname": name,
        "email": email,
        "phone": phone,
        "productinfo": product
    }

    # Bind explicit execution routing options if selected by testing agent
    if mode.upper() != "ALL":
        payload["payment_mode"] = mode.upper()

    extra_args = collect_dynamic_args(ctx, interactive, PAYMENT_INITIATE_SCHEMA)

    with console.status(f"[bold magenta]Contacting Easebuzz {current_env.upper()} servers..."):
        txnid, final_payload, endpoint_url, res_data = initiate_payment_logic(config, payload, extra_args)


    # Output the exact curl block for merchant copy-pasting
    display_diagnostic_curl(endpoint_url, payload)

    if res_data.get("status") == 1:
        console.print("\n[bold green]Transaction initiated successfully![/bold green]")
        table = Table(title=f"Transaction Summary ({current_env.upper()})")
        table.add_column("Parameter", style="cyan")
        table.add_column("Value", style="magenta")
        table.add_row("Transaction ID", txnid)
        table.add_row("Amount", f"INR {amount:.2f}")

        console.print(table)
        console.print(Panel(f"[bold cyan] Payment Link:[/bold cyan]\n{res_data.get('data')}", title="Action Data"))
    else:
        console.print(f"\n[bold red] Initiation Failed:[/bold red]")
        console.print_json(data=res_data)


@payments_app.command(
    "bulk",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def bulk_payment(
        ctx: typer.Context,
        count: int = typer.Option(5, "--count", "-c", help="Number of distinct unique executions"),
        amount: float = typer.Option(10.00, "--amount", "-a", help="Base static fallback processing currency tier")
):
    config = init_config()

    if not config.get("key") or not config.get("salt"):
        console.print("[bold red]Error: CLI not configured. Run 'easebuzz configure' first.[/bold red]")
        raise typer.Exit(code=1)

    current_env = config.get("env", "sandbox")
    endpoint_url = get_active_endpoint("initiate", "")

    console.print(
        f"[bold magenta]Dispatching {count} concurrent bulk workers against {current_env.upper()} endpoint...[/bold magenta]\n")

    # --- 1. PARSE DYNAMIC EXTRA ARGS ---
    extra_args = {}
    if ctx.args:
        for i in range(0, len(ctx.args), 2):
            flag = ctx.args[i].lstrip("-")
            if flag in PAYMENT_INITIATE_SCHEMA["optional"]:
                val = ctx.args[i + 1] if i + 1 < len(ctx.args) else ""
                extra_args[flag] = val

    if extra_args:
        console.print(f"[bold cyan]ℹ️ Injecting explicit batch arguments:[bold cyan] {extra_args}\n")

    # --- 2. GENERATE TRULY RANDOMIZED PAYLOADS WITH FAKER ---
    payloads_pool = []

    fake = Faker('en_IN')
    mock_products = ["SaaS_License", "Cloud_Credits", "API_Premium_Pack", "Dev_Testing_Stub", "Ecom_Cart",
                     "Wallet_Topup"]
    mock_modes = ["ALL", "UPI", "NB", "CC", "DC"]

    for _ in range(count):
        txnid = generate_txnid()

        # Generate realistic first name using Faker
        random_firstname = fake.first_name()

        # Base Mandatory Fields
        mock_payload = {
            "key": config.get("key"),
            "txnid": txnid,
            "amount": f"{amount + random.uniform(1.0, 99.0):.2f}",
            "firstname": random_firstname,
            "email": f"{random_firstname.lower()}.{secrets.token_hex(3)}@easebuzz-test.in",
            "phone": f"9{random.randint(100000001, 999999999)}",
            # Keep phone static-ish for strict validation bypass if needed, or use fake.phone_number()
            "productinfo": random.choice(mock_products),
            "surl": "https://localhost/success",
            "furl": "https://localhost/failure"
        }

        # Randomized Payment Mode
        chosen_mode = random.choice(mock_modes)
        if chosen_mode != "ALL":
            mock_payload["payment_mode"] = chosen_mode

        # Realistic Geo-Data via Faker
        if random.choice([True, False]):
            mock_payload["city"] = fake.city()
            mock_payload["state"] = fake.state()  # Generates full state names like "Maharashtra"
            mock_payload["zipcode"] = fake.postcode()

        if random.random() < 0.3:
            mock_payload["udf1"] = f"cohort_{random.randint(1, 10)}"
        if random.random() < 0.3:
            mock_payload["udf2"] = random.choice(["ios_app", "android_app", "mobile_web", "desktop"])

        if chosen_mode != "ALL" and random.random() < 0.2:
            mock_payload["show_payment_mode"] = chosen_mode

        # Override randomization with explicit CLI args
        mock_payload.update(extra_args)

        # Hash it AFTER all fields are assembled
        mock_payload["hash"] = generate_hash(mock_payload, config.get("salt"))
        payloads_pool.append(mock_payload)

    # --- 3. CONCURRENT EXECUTION ---
    results_table = Table(title=f"Asynchronous Batch Run Summary ({current_env.upper()})")
    results_table.add_column("Worker", style="dim cyan", justify="center")
    results_table.add_column("Transaction ID", style="magenta")
    results_table.add_column("Mode", style="yellow")
    results_table.add_column("Amount", style="green")
    results_table.add_column("Gateway Diagnostic Verdict", style="bold white")

    with console.status("[bold yellow]Executing parallel workers..."):
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(count, 10)) as executor:
            futures = {
                executor.submit(post_execute_single_payload, endpoint_url, p): p
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