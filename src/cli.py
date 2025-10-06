import typer

from bot.main import start_bot

cli = typer.Typer()

@cli.command()
def start() -> None:
    start_bot()


if __name__ == '__main__':
    cli()
