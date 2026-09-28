"""Конфигурация приложения.

Настройки читаются (в порядке убывания приоритета) из аргументов конструктора,
переменных окружения с префиксом ``RG_`` и файла ``.env`` в текущей директории.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LogFormat = Literal["text", "json"]

_LEVELS = frozenset({"debug", "info", "warning", "error", "critical"})


class Settings(BaseSettings):
    """Настройки research-graph."""

    model_config = SettingsConfigDict(
        env_prefix="RG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        validate_default=True,
    )

    github_token: SecretStr | None = Field(
        default=None,
        description="Персональный токен GitHub для запросов к API.",
    )
    data_dir: Path = Field(
        default=Path("data"),
        description="Корневая директория для данных (снимки, Bronze/Silver/Gold).",
    )
    log_level: LogLevel = Field(default="INFO", description="Уровень логирования.")
    log_format: LogFormat = Field(default="text", description="Формат логов: text или json.")
    request_timeout: float = Field(
        default=10.0,
        gt=0,
        le=300,
        description="Таймаут HTTP-запросов, секунды.",
    )
    max_concurrency: int = Field(
        default=4,
        ge=1,
        le=64,
        description="Максимум одновременных запросов.",
    )

    @field_validator("log_level", "log_format", mode="before")
    @classmethod
    def _normalize_case(cls, value: object) -> object:
        """Позволяет писать ``RG_LOG_LEVEL=debug`` и ``RG_LOG_FORMAT=JSON``."""
        if isinstance(value, str):
            value = value.strip()
            return value.upper() if value.lower() in _LEVELS else value.lower()
        return value

    @field_validator("github_token", mode="before")
    @classmethod
    def _empty_token_is_none(cls, value: object) -> object:
        """Пустая строка в ``.env`` означает «токена нет»."""
        if isinstance(value, str) and not value.strip():
            return None
        return value

    def ensure_data_dir(self) -> Path:
        """Создаёт ``data_dir`` (если его нет) и возвращает абсолютный путь."""
        path = self.data_dir.expanduser().resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    def masked_token(self) -> str:
        """Безопасное представление токена для вывода: ``ghp_****abcd``."""
        return mask_secret(self.github_token)


def mask_secret(secret: SecretStr | None, visible: int = 4) -> str:
    """Маскирует секрет, оставляя префикс (до ``_``) и последние ``visible`` символов.

    Короткие значения скрываются полностью, чтобы по маске нельзя было
    восстановить заметную часть секрета.
    """
    if secret is None:
        return "<not set>"
    raw = secret.get_secret_value()
    if len(raw) <= visible * 3:
        return "****"
    prefix, sep, _ = raw.partition("_")
    head = f"{prefix}{sep}" if sep and len(prefix) <= 4 else ""
    return f"{head}****{raw[-visible:]}"


def get_settings() -> Settings:
    """Возвращает экземпляр настроек, прочитанный из окружения и ``.env``."""
    return Settings()
