from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError

from research_graph.config import Settings, get_settings, mask_secret


def test_defaults_without_env() -> None:
    settings = get_settings()
    assert settings.github_token is None
    assert settings.data_dir == Path("data")
    assert settings.log_level == "INFO"
    assert settings.log_format == "text"
    assert settings.request_timeout == 10.0
    assert settings.max_concurrency == 4


def test_settings_read_from_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("RG_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("RG_MAX_CONCURRENCY", "16")
    monkeypatch.setenv("RG_REQUEST_TIMEOUT", "2.5")
    monkeypatch.setenv("RG_DATA_DIR", str(tmp_path / "rg-data"))
    settings = Settings()
    assert settings.log_level == "DEBUG"
    assert settings.max_concurrency == 16
    assert settings.request_timeout == 2.5
    assert settings.data_dir == tmp_path / "rg-data"


def test_settings_read_from_dotenv(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text(
        "RG_LOG_LEVEL=WARNING\nRG_GITHUB_TOKEN=ghp_fromdotenvfile1234\n", encoding="utf-8"
    )
    settings = Settings()
    assert settings.log_level == "WARNING"
    assert settings.github_token is not None
    assert settings.github_token.get_secret_value() == "ghp_fromdotenvfile1234"


def test_env_overrides_dotenv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / ".env").write_text("RG_MAX_CONCURRENCY=2\n", encoding="utf-8")
    monkeypatch.setenv("RG_MAX_CONCURRENCY", "8")
    assert Settings().max_concurrency == 8


@pytest.mark.parametrize(
    ("raw_level", "expected"),
    [("debug", "DEBUG"), (" Warning ", "WARNING"), ("ERROR", "ERROR")],
)
def test_log_level_is_case_insensitive(
    monkeypatch: pytest.MonkeyPatch, raw_level: str, expected: str
) -> None:
    monkeypatch.setenv("RG_LOG_LEVEL", raw_level)
    assert Settings().log_level == expected


def test_log_format_is_case_insensitive(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RG_LOG_FORMAT", "JSON")
    assert Settings().log_format == "json"


def test_empty_token_means_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RG_GITHUB_TOKEN", "  ")
    assert Settings().github_token is None


def test_token_not_leaked_in_repr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RG_GITHUB_TOKEN", "ghp_supersecretvalue")
    settings = Settings()
    assert "ghp_supersecretvalue" not in repr(settings)
    assert "ghp_supersecretvalue" not in str(settings.model_dump())


def test_rejects_invalid_concurrency(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RG_MAX_CONCURRENCY", "0")
    with pytest.raises(ValidationError):
        Settings()


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("RG_MAX_CONCURRENCY", "65"),
        ("RG_MAX_CONCURRENCY", "many"),
        ("RG_REQUEST_TIMEOUT", "0"),
        ("RG_REQUEST_TIMEOUT", "-1"),
        ("RG_REQUEST_TIMEOUT", "301"),
        ("RG_LOG_LEVEL", "VERBOSE"),
        ("RG_LOG_FORMAT", "xml"),
    ],
)
def test_rejects_out_of_range_values(monkeypatch: pytest.MonkeyPatch, key: str, value: str) -> None:
    monkeypatch.setenv(key, value)
    with pytest.raises(ValidationError):
        Settings()


def test_rejects_non_string_log_level() -> None:
    with pytest.raises(ValidationError):
        Settings(log_level=10)  # type: ignore[arg-type]  # проверяем валидацию неверного типа


def test_ensure_data_dir_creates_directory(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "data"
    settings = Settings(data_dir=target)
    created = settings.ensure_data_dir()
    assert created == target.resolve()
    assert created.is_dir()
    # повторный вызов не падает
    assert settings.ensure_data_dir() == created


@pytest.mark.parametrize(
    ("secret", "expected"),
    [
        (None, "<not set>"),
        ("short", "****"),
        ("ghp_supersecretvalue", "ghp_****alue"),
        ("github_pat_11ABCDEFG0123456789_xyzw", "****xyzw"),
        ("plainsecretwithoutprefix", "****efix"),
    ],
)
def test_mask_secret(secret: str | None, expected: str) -> None:
    value = SecretStr(secret) if secret is not None else None
    assert mask_secret(value) == expected


def test_masked_token_method(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RG_GITHUB_TOKEN", "ghp_abcdefghijklmnop")
    assert Settings().masked_token() == "ghp_****mnop"
