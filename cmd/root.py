import typer

from cmd.payments.make_payment import payments_app
from cmd.payments.make_seamless_payment import seamless_payments_app
from cmd.payments.payment_status import payments_status_app
from config.config import console
from cmd.configure import configure

__version__ = "1.1.0"
LONG_DESCRIPTION = """
The Easebuzz CLI provides command-line access to the Easebuzz API.

To get started, configure your API credentials:

  [bold cyan]easebuzz configure[/bold cyan]

Then run any resource command, for example:

  [bold cyan]easebuzz payment initiate --amount 500.00[/bold cyan]
  [bold cyan]easebuzz payment bulk --count 10[/bold cyan]

For help on a specific command, run:

  [bold cyan]easebuzz <command> --help[/bold cyan]
"""

root_app = typer.Typer(
    name="easebuzz",
    no_args_is_help=True,
    rich_markup_mode="rich",
    help=LONG_DESCRIPTION
)

root_app.command(name="configure")(configure)
root_app.add_typer(payments_app, name="payment")
root_app.add_typer(seamless_payments_app, name="seamless")
root_app.add_typer(payments_status_app, name="payment-status")

def version_callback(value: bool):
    if value:
        console.print(f"[bold cyan]Easebuzz-CLI Version:[/bold cyan] {__version__}")
        raise typer.Exit()

@root_app.callback()
def global_options(
    ctx: typer.Context,
    version: bool = typer.Option(
        None, "--version", "-v",
        callback=version_callback,
        is_eager=True,
        help="Print version information and exit."
    )
):
    pass