import typer

from bot.main import start_bot

cli = typer.Typer()

@cli.command()
def start() -> None:
    start_bot()

@cli.command()
def dummy() -> None:
    typer.echo("This is a dummy command. It does nothing.")


if __name__ == '__main__':
    cli()
