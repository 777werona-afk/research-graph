"""Настройка логирования приложения.

Логи всегда пишутся в ``stderr``: ``stdout`` оставлен для данных,
которые CLI может отдавать в пайп.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Final, Literal

TEXT_FORMAT: Final = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
DATE_FORMAT: Final = "%Y-%m-%dT%H:%M:%S%z"

#: Сторонние библиотеки, которые слишком многословны на уровне DEBUG/INFO.
NOISY_LOGGERS: Final = ("httpx", "httpcore", "urllib3", "asyncio", "markdown_it")

#: Стандартные атрибуты LogRecord — всё остальное считаем пользовательским ``extra``.
_RESERVED_ATTRS: Final = frozenset(
    vars(logging.LogRecord("", 0, "", 0, "", None, None)).keys() | {"message", "asctime"}
)


class JsonFormatter(logging.Formatter):
    """Форматирует запись как одну JSON-строку."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        for key, value in vars(record).items():
            if key not in _RESERVED_ATTRS and not key.startswith("_"):
                payload[key] = value
        return json.dumps(payload, ensure_ascii=False, default=str)


def setup_logging(level: str, fmt: Literal["text", "json"] = "text") -> None:
    """Настраивает корневой логгер.

    Повторный вызов безопасен: существующие обработчики удаляются,
    поэтому записи не задваиваются (актуально для тестов).
    """
    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)
        handler.close()

    handler = logging.StreamHandler(sys.stderr)
    formatter: logging.Formatter = (
        JsonFormatter() if fmt == "json" else logging.Formatter(TEXT_FORMAT, DATE_FORMAT)
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.setLevel(level.upper())

    for name in NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
