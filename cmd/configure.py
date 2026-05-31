import typer
from config.config import console, save, ENV_URLS


def configure(
    key: str = typer.Option(..., "--key", "-k", prompt="Enter Easebuzz Merchant Key", hide_input=True),
    salt: str = typer.Option(..., "--salt", "-s", prompt="Enter Easebuzz Merchant Salt", hide_input=True),
    env: str = typer.Option("sandbox", "--env", "-e", prompt="Environment (development/qa/sandbox/production)")
):
    if not key.strip() or not salt.strip():
        console.print("[bold red]Error: Key and Salt cannot be empty.[/bold red]")
        raise typer.Exit(code=1)

    env = env.lower().strip()
    if env not in ENV_URLS:
        console.print(
            f"[bold red]Error: Invalid environment '{env}'. Choose from: {', '.join(ENV_URLS.keys())}.[/bold red]")
        raise typer.Exit(code=1)

    err = save(key, salt, env)
    if err is not None:
        console.print(f"[bold red]Error saving configurations: {err}[/bold red]")
        raise typer.Exit(code=1)

    console.print("[bold green]✔ Configuration saved successfully to your home directory.[/bold green]")