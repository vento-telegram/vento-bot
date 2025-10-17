import typer

from bot.main import start_bot
from bot.admin_main import start_admin_bot

cli = typer.Typer()

@cli.command()
def start() -> None:
    start_bot()

@cli.command()
def start_admin() -> None:
    start_admin_bot()


if __name__ == '__main__':
    cli()
