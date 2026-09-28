from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from research_graph import __version__
from research_graph.cli import app

runner = CliRunner()


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == __version__


def test_help_lists_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "version" in result.stdout
    assert "check-config" in result.stdout


def test_no_args_shows_help() -> None:
    result = runner.invoke(app, [])
    assert "check-config" in result.output


def test_check_config_prints_summary() -> None:
    result = runner.invoke(app, ["check-config"])
    assert result.exit_code == 0
    assert "github_token" in result.stdout
    assert "<not set>" in result.stdout
    assert "max_concurrency" in result.stdout


def test_check_config_hides_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RG_GITHUB_TOKEN", "ghp_supersecretvalue")
    result = runner.invoke(app, ["check-config"])
    assert result.exit_code == 0
    assert "ghp_supersecretvalue" not in result.stdout
    assert "ghp_supersecretvalue" not in result.output
    assert "ghp_****alue" in result.stdout


def test_check_config_uses_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RG_MAX_CONCURRENCY", "12")
    monkeypatch.setenv("RG_LOG_FORMAT", "json")
    result = runner.invoke(app, ["check-config"])
    assert result.exit_code == 0
    assert "12" in result.stdout
    assert "json" in result.stdout


def test_check_config_create_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "store"
    monkeypatch.setenv("RG_DATA_DIR", str(target))
    result = runner.invoke(app, ["check-config", "--create-dirs"])
    assert result.exit_code == 0
    assert target.is_dir()


def test_check_config_invalid_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RG_MAX_CONCURRENCY", "0")
    result = runner.invoke(app, ["check-config"])
    assert result.exit_code == 2
    assert "Ошибка конфигурации" in result.output


def test_check_config_logs_json_to_stderr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RG_LOG_FORMAT", "json")
    monkeypatch.setenv("RG_GITHUB_TOKEN", "ghp_supersecretvalue")
    result = runner.invoke(app, ["check-config"])
    assert result.exit_code == 0
    assert "ghp_supersecretvalue" not in result.output
    json_lines = [line for line in result.output.splitlines() if line.startswith("{")]
    assert json_lines
    assert json.loads(json_lines[0])["message"] == "Конфигурация загружена"
