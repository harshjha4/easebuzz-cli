import typer

from cmd.payments.make_payment import payments_app
from config.config import console
from cmd.configure import configure

__version__ = "1.0.0"

root_app = typer.Typer(
    name="easebuzz",
    help="Streamlined Dev-Tooling for Testing Easebuzz Merchant Integrations."
)

root_app.command(name="configure")(configure)
root_app.add_typer(payments_app, name="payment")

def version_callback(value: bool):
    if value:
        console.print(f"[bold cyan]Easebuzz-CLI Version:[/bold cyan] {__version__}")
        raise typer.Exit()

@root_app.callback()
def global_options(
    version: bool = typer.Option(
        None, "--version", "-v",
        callback=version_callback,
        is_eager=True,
        help="Print version information and exit."
    )
):
    """
    Global control hook processing global option states.
    """
    pass