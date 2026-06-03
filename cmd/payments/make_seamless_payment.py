import typer
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from config.config import console, init_config, display_diagnostic_curl, collect_dynamic_args
from config.constants import PAYMENT_INITIATE_SCHEMA, SEAMLESS_INSTRUMENT_SCHEMA
from services.payments import initiate_payment_logic, seamless_payment_logic

seamless_payments_app = typer.Typer(help="Execute Server-to-Server seamless payments directly from the CLI.")


@seamless_payments_app.command("initiate")
def seamless_payment(
        # --- Mandatory Fields ---
        amount: float = typer.Option(..., prompt="Enter payment amount"),
        name: str = typer.Option(..., prompt="Customer First Name"),
        email: str = typer.Option(..., prompt="Customer Email ID"),
        phone: str = typer.Option(..., prompt="Customer Mobile Number"),
        product: str = typer.Option("CLI_Purchase", prompt="Product Info/Description"),

        # --- Execution Modifiers ---
        mode: str = typer.Option(..., "--mode", "-m", prompt="Payment Mode (CC, DC, NB, UPI, EMI)"),
        interactive: bool = typer.Option(False, "--interactive", "-i",
                                         help="Launch the dynamic wizard for optional initiate fields."),

        # --- Config Overrides ---
        key: str = typer.Option(None, "--key", help="Override Merchant Key for this execution"),
        salt: str = typer.Option(None, "--salt",
                                       help="Override Merchant Salt/Secret for this execution"),
        env: str = typer.Option(None, "--env", help="Override Target Environment (sandbox/dev/production)"),

        # --- Explicit Optional Fields (Matches initiate pattern) ---
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
        sub_merchant_id: str = typer.Option(None, help="Sub Merchant ID"),
        unique_id: str = typer.Option(None, help="Unique Identifier")
):
    config = init_config()

    if key: config["key"] = key
    if salt: config["salt"] = salt
    if env: config["env"] = env.lower()

    current_env = config.get("env", "sandbox")
    mode = mode.upper()

    if mode not in SEAMLESS_INSTRUMENT_SCHEMA:
        valid_modes = ", ".join(SEAMLESS_INSTRUMENT_SCHEMA.keys())
        console.print(f"[bold red]Error: Mode must be one of {valid_modes}.[/bold red]")
        raise typer.Exit(1)

    # 1. DYNAMICALLY BUNDLE EXPLICIT ARGS
    func_vars = locals()
    current_args = {k: func_vars[k] for k in PAYMENT_INITIATE_SCHEMA if func_vars.get(k) is not None}

    # 2. RUN THE WIZARD (For optional payload fields)
    extra_args = collect_dynamic_args(interactive, PAYMENT_INITIATE_SCHEMA, current_args)

    console.print(f"\n[bold cyan]--- Step 1: Initiating Secure Session ({current_env.upper()}) ---[/bold cyan]")
    base_payload = {
        "amount": f"{amount:.2f}",
        "firstname": name,
        "email": email,
        "phone": phone,
        "productinfo": product,
        "request_flow": "SEAMLESS"
    }

    with console.status("[bold blue]Fetching secure access_key..."):
        txnid, init_payload, init_url, init_res = initiate_payment_logic(config, base_payload, extra_args)

    if init_res.get("status") != 1:
        console.print(f"\n[bold red] Handshake Failed: Could not acquire Access Key.[/bold red]")
        console.print_json(data=init_res)
        raise typer.Exit(1)

    access_key = init_res.get("data")
    console.print(f"[bold green] Secure Session Created! Access Key:[/bold green] {access_key}")

    # Step 2: Processing Seamless Payment (Context Aware Prompts)
    console.print(f"\n[bold cyan]--- Step 2: Processing Seamless Payment ({mode}) ---[/bold cyan]")
    instrument_details = {}
    mode_schema = SEAMLESS_INSTRUMENT_SCHEMA[mode]

    console.print("[dim white]Please enter the required payment instrument details:[/dim white]")
    for field_key, prompt_label in mode_schema.items():
        # Mask sensitive CVV inputs automatically
        is_secret = "cvv" in field_key.lower()
        user_input = Prompt.ask(f"  [magenta]>[/magenta] {prompt_label}", password=is_secret)
        instrument_details[field_key] = user_input

    # Easebuzz specific UPI requirement
    if mode == "UPI":
        instrument_details["request_mode"] = "SUVA"

    with console.status(f"[bold magenta]Pushing encrypted instrument payload to {current_env.upper()}..."):
        seamless_payload, seamless_url, seamless_res = seamless_payment_logic(
            config, access_key, mode, instrument_details
        )

    # Diagnostics
    console.print("\n")
    display_diagnostic_curl(seamless_url, seamless_payload)

    if isinstance(seamless_res, dict) and seamless_res.get("status") == 0:
        console.print(f"\n[bold red] Seamless Transaction Failed:[/bold red]")
        console.print_json(data=seamless_res)
    else:
        console.print("\n[bold green] Seamless Transaction Handshake Completed![/bold green]")

        # Displaying a clean summary table for the final seamless response
        table = Table(title="S2S Gateway Response")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="white")

        if isinstance(seamless_res, dict):
            for k, v in seamless_res.items():
                # Truncate deeply nested dicts/lists for terminal readability
                if isinstance(v, (dict, list)):
                    table.add_row(str(k), "[dim]...[Nested Data]...[/dim]")
                else:
                    table.add_row(str(k), str(v))
            console.print(table)
        else:
            console.print(Panel(f"{str(seamless_res)[:700]}...", title="Raw Response"))