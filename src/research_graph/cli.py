"""Командная строка ``rg``."""

from __future__ import annotations

import logging
from typing import Annotated

import typer
from pydantic import ValidationError

from research_graph import __version__
from research_graph.config import get_settings
from research_graph.logging_setup import setup_logging

app = typer.Typer(
    name="rg",
    help="research-graph: инструменты для построения графа исследований.",
    no_args_is_help=True,
    add_completion=False,
)

logger = logging.getLogger(__name__)


@app.command()
def version() -> None:
    """Показать версию пакета."""
    typer.echo(__version__)


@app.command("check-config")
def check_config(
    create_dirs: Annotated[
        bool,
        typer.Option("--create-dirs", help="Создать data_dir, если её нет."),
    ] = False,
) -> None:
    """Загрузить настройки, включить логирование и вывести сводку (без секретов)."""
    try:
        settings = get_settings()
    except ValidationError as exc:
        typer.echo(f"Ошибка конфигурации:\n{exc}", err=True)
        raise typer.Exit(code=2) from exc

    setup_logging(settings.log_level, settings.log_format)
    logger.info("Конфигурация загружена")

    data_dir = settings.ensure_data_dir() if create_dirs else settings.data_dir

    rows = {
        "github_token": settings.masked_token(),
        "data_dir": str(data_dir),
        "log_level": settings.log_level,
        "log_format": settings.log_format,
        "request_timeout": f"{settings.request_timeout:g} s",
        "max_concurrency": str(settings.max_concurrency),
    }
    width = max(len(key) for key in rows)
    typer.echo("research-graph configuration:")
    for key, value in rows.items():
        typer.echo(f"  {key:<{width}}  {value}")


def main() -> None:  # pragma: no cover - тонкая обёртка для python -m
    app()
