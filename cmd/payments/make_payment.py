import concurrent.futures
import random
import secrets

import typer
from rich.panel import Panel
from faker import Faker
from rich.table import Table

from config.config import console, init_config, generate_txnid, generate_hash, get_active_endpoint, \
    display_diagnostic_curl, post_execute_single_payload, collect_dynamic_args
from config.constants import PAYMENT_INITIATE_SCHEMA
from services.payments import initiate_payment_logic

payments_app = typer.Typer(help="Execute manual, targeted mode, and asynchronous bulk payment simulations.")


@payments_app.command("initiate")
def initiate_payment(
        # --- Mandatory Fields ---
        amount: float = typer.Option(..., prompt="Enter payment amount (e.g., 50.00)"),
        name: str = typer.Option(..., prompt="Customer First Name"),
        email: str = typer.Option(..., prompt="Customer Email ID"),
        phone: str = typer.Option(..., prompt="Customer Mobile Number"),
        product: str = typer.Option("CLI_Purchase", prompt="Product Info/Description"),

        # --- Execution Modifiers ---
        mode: str = typer.Option("ALL", "--mode", "-m", help="Restrict payment methods: NB, CC, DC, UPI, or ALL"),
        interactive: bool = typer.Option(False, "--interactive", "-i",
                                         help="Launch the dynamic wizard to include optional fields."),

        # --- Config Overrides ---
        key: str = typer.Option(None, "--key", help="Override Merchant Key for this execution"),
        salt: str = typer.Option(None,  "--salt",
                                       help="Override Merchant Salt/Secret for this execution"),
        env: str = typer.Option(None, "--env", help="Override Target Environment (sandbox/dev/production)"),

        # --- Explicit Optional Fields ---
        udf1: str = typer.Option(None, help="User Defined Field 1"),
        udf2: str = typer.Option(None, help="User Defined Field 2"),
        udf3: str = typer.Option(None, help="User Defined Field 3"),
        udf4: str = typer.Option(None, help="User Defined Field 4"),
        udf5: str = typer.Option(None, help="User Defined Field 5"),
        udf6: str = typer.Option(None, help="User Defined Field 6"),
        udf7: str = typer.Option(None, help="User Defined Field 7"),
        address1: str = typer.Option(None, help="Billing Address Line 1"),
        address2: str = typer.Option(None, help="Billing Address Line 2"),
        city: str = typer.Option(None, help="City"),
        state: str = typer.Option(None, help="State"),
        country: str = typer.Option(None, help="Country"),
        zipcode: str = typer.Option(None, help="Zip/Postal Code"),
        show_payment_mode: str = typer.Option(None, help="Show Payment Mode"),
        split_payments: str = typer.Option(None, help="Split Payments Array"),
        request_flow: str = typer.Option(None, help="Request Flow"),
        sub_merchant_id: str = typer.Option(None, help="Sub Merchant ID"),
        payment_category: str = typer.Option(None, help="Payment Category"),
        account_no: str = typer.Option(None, help="Account Number"),
        ifsc: str = typer.Option(None, help="IFSC Code"),
        unique_id: str = typer.Option(None, help="Unique Identifier")
):
    """Generate and dispatch a new payment transaction link to Easebuzz."""
    config = init_config()

    if key: config["key"] = key
    if salt: config["salt"] = salt
    if env: config["env"] = env.lower()

    if not config.get("key") or not config.get("salt"):
        console.print("[bold red]CLI unconfigured. Pass --key and --secret, or run 'easebuzz configure'.[/bold red]")
        raise typer.Exit(1)

    current_env = config.get("env", "sandbox")
    endpoint_url = get_active_endpoint('initiate', "/payment/initiateLink")

    # 1. BUNDLE THE EXPLICIT ARGS
    explicit_args = {
        "udf1": udf1, "udf2": udf2, "udf3": udf3, "udf4": udf4, "udf5": udf5, "udf6": udf6, "udf7": udf7,
        "address1": address1, "address2": address2, "city": city, "state": state, "country": country,
        "zipcode": zipcode, "show_payment_mode": show_payment_mode, "split_payments": split_payments,
        "request_flow": request_flow, "sub_merchant_id": sub_merchant_id, "payment_category": payment_category,
        "account_no": account_no, "ifsc": ifsc, "unique_id": unique_id
    }
    # Remove empty ones
    current_args = {k: v for k, v in explicit_args.items() if v is not None}

    # 2. RUN THE WIZARD (Pass all 3 arguments!)
    extra_args = collect_dynamic_args(interactive, PAYMENT_INITIATE_SCHEMA, current_args)

    payload = {
        "amount": f"{amount:.2f}",
        "firstname": name,
        "email": email,
        "phone": phone,
        "productinfo": product
    }

    if mode.upper() != "ALL":
        payload["payment_mode"] = mode.upper()

    with console.status(f"[bold magenta]Contacting Easebuzz {current_env.upper()} servers..."):
        txnid, final_payload, endpoint_url, res_data = initiate_payment_logic(config, payload, extra_args)

    display_diagnostic_curl(endpoint_url, final_payload)

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


@payments_app.command("bulk")
def bulk_payment(
        count: int = typer.Option(5, "--count", "-c", help="Number of distinct unique executions"),
        amount: float = typer.Option(10.00, "--amount", "-a", help="Base static fallback processing currency tier"),

        # --- Config Overrides ---
        key: str = typer.Option(None, "--key", help="Override Merchant Key for this execution"),
        salt: str = typer.Option(None,  "--salt",
                                       help="Override Merchant Salt/Secret for this execution"),
        env: str = typer.Option(None, "--env", help="Override Target Environment (sandbox/dev/production)"),

        # --- Explicit Optional Fields ---
        udf1: str = typer.Option(None, help="User Defined Field 1"),
        udf2: str = typer.Option(None, help="User Defined Field 2"),
        city: str = typer.Option(None, help="City"),
        state: str = typer.Option(None, help="State"),
        zipcode: str = typer.Option(None, help="Zip/Postal Code")
):
    config = init_config()

    if key: config["key"] = key
    if salt: config["salt"] = salt
    if env: config["env"] = env.lower()

    if not config.get("key") or not config.get("salt"):
        console.print(
            "[bold red]Error: CLI not configured. Pass --key and --secret, or run 'easebuzz configure'.[/bold red]")
        raise typer.Exit(code=1)

    current_env = config.get("env", "sandbox")
    endpoint_url = get_active_endpoint("initiate", "")

    console.print(
        f"[bold magenta]Dispatching {count} concurrent bulk workers against {current_env.upper()} endpoint...[/bold magenta]\n")

    # 1. BUNDLE THE EXPLICIT ARGS FOR BULK
    explicit_args = {"udf1": udf1, "udf2": udf2, "city": city, "state": state, "zipcode": zipcode}
    extra_args = {k: v for k, v in explicit_args.items() if v is not None}

    if extra_args:
        console.print(f"[bold cyan] Injecting explicit batch arguments:[bold cyan] {extra_args}\n")

    # --- 2. GENERATE TRULY RANDOMIZED PAYLOADS WITH FAKER ---
    payloads_pool = []
    fake = Faker('en_IN')
    mock_products = ["SaaS_License", "Cloud_Credits", "API_Premium_Pack", "Dev_Testing_Stub", "Ecom_Cart",
                     "Wallet_Topup"]
    mock_modes = ["ALL", "UPI", "NB", "CC", "DC"]

    for _ in range(count):
        txnid = generate_txnid()
        random_firstname = fake.first_name()

        mock_payload = {
            "key": config.get("key"),
            "txnid": txnid,
            "amount": f"{amount + random.uniform(1.0, 99.0):.2f}",
            "firstname": random_firstname,
            "email": f"{random_firstname.lower()}.{secrets.token_hex(3)}@easebuzz-test.in",
            "phone": f"9{random.randint(100000001, 999999999)}",
            "productinfo": random.choice(mock_products),
            "surl": "https://localhost/success",
            "furl": "https://localhost/failure"
        }

        chosen_mode = random.choice(mock_modes)
        if chosen_mode != "ALL": mock_payload["payment_mode"] = chosen_mode

        if random.choice([True, False]):
            mock_payload["city"] = fake.city()
            mock_payload["state"] = fake.state()
            mock_payload["zipcode"] = fake.postcode()

        if random.random() < 0.3: mock_payload["udf1"] = f"cohort_{random.randint(1, 10)}"
        if random.random() < 0.3: mock_payload["udf2"] = random.choice(
            ["ios_app", "android_app", "mobile_web", "desktop"])
        if chosen_mode != "ALL" and random.random() < 0.2: mock_payload["show_payment_mode"] = chosen_mode

        # Explicit overrides take priority over Faker
        mock_payload.update(extra_args)

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