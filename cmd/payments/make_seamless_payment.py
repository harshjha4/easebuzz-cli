import typer
from rich.panel import Panel
from rich.prompt import Prompt

from config.config import console, init_config, display_diagnostic_curl, collect_dynamic_args
from config.constants import PAYMENT_INITIATE_SCHEMA, SEAMLESS_INSTRUMENT_SCHEMA
from services.payments import initiate_payment_logic, seamless_payment_logic

seamless_payments_app = typer.Typer(help="Execute seamless payments")

@seamless_payments_app.command("seamless", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def seamless_payment(
        ctx: typer.Context,
        amount: float = typer.Option(..., prompt="Enter payment amount"),
        name: str = typer.Option(..., prompt="Customer First Name"),
        email: str = typer.Option(..., prompt="Customer Email ID"),
        phone: str = typer.Option(..., prompt="Customer Mobile Number"),
        product: str = typer.Option("CLI_Purchase", prompt="Product Info/Description"),
        mode: str = typer.Option(..., "--mode", "-m", prompt="Payment Mode (CC, DC, NB, UPI)"),
        interactive: bool = typer.Option(False, "--interactive", "-i")
):
    config = init_config()
    current_env = config.get("env", "sandbox")
    mode = mode.upper()

    if mode not in SEAMLESS_INSTRUMENT_SCHEMA:
        valid_modes = ", ".join(SEAMLESS_INSTRUMENT_SCHEMA.keys())
        console.print(f"[bold red]Error: Mode must be {valid_modes}.[/bold red]")
        raise typer.Exit(1)

    # 1. Collect Args & Initiate (Step 1)
    console.print(f"\n[bold cyan]--- Step 1: Initiating Secure Session ({current_env.upper()}) ---[/bold cyan]")
    base_payload = {
        "amount": f"{amount:.2f}",
        "firstname": name,
        "email": email,
        "phone": phone,
        "productinfo": product
    }
    extra_args = collect_dynamic_args(ctx, interactive, PAYMENT_INITIATE_SCHEMA)

    with console.status("[bold blue]Fetching secure access_key..."):
        txnid, init_payload, init_url, init_res = initiate_payment_logic(config, base_payload, extra_args)

    if init_res.get("status") != 1:
        console.print(f"\n[bold red] Initiation Failed.[/bold red]")
        console.print_json(data=init_res)
        raise typer.Exit(1)

    access_key = init_res.get("data")
    console.print(f"[bold green] Secure Session Created! Access Key:[/bold green] {access_key}")

    # step-2 Processing Seamless Payment
    console.print(f"\n[bold cyan]--- Step 2: Processing Seamless Payment ---[/bold cyan]")
    instrument_details = {}
    mode_schema = SEAMLESS_INSTRUMENT_SCHEMA[mode]

    for field_key, prompt_label in mode_schema.items():
        is_secret = "cvv" in field_key.lower()

        user_input = Prompt.ask(f"{prompt_label}", password=is_secret)
        instrument_details[field_key] = user_input

    if mode == "UPI":
        instrument_details["request_mode"] = "SUVA"

    with console.status(f"[bold magenta]Pushing Instrument Details to {current_env.upper()}..."):
        seamless_payload, seamless_url, seamless_res = seamless_payment_logic(
            config, access_key, mode, instrument_details
        )

    display_diagnostic_curl(seamless_url, seamless_payload)

    if isinstance(seamless_res, dict) and seamless_res.get("status") == 0:
        console.print(f"\n[bold red] Seamless Transaction Failed:[/bold red]")
        console.print_json(data=seamless_res)
    else:
        console.print("\n[bold green] Seamless Transaction Handshake Completed![/bold green]")
        console.print(Panel(f"{str(seamless_res)[:700]}... [Truncated]", title="Easebuzz API Response"))