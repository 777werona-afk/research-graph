from __future__ import annotations

import json
import logging
import sys

import pytest

from research_graph.logging_setup import NOISY_LOGGERS, JsonFormatter, setup_logging


def test_setup_logging_writes_to_stderr(capsys: pytest.CaptureFixture[str]) -> None:
    setup_logging("INFO")
    logging.getLogger("research_graph.test").info("hello")
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "INFO" in captured.err
    assert "research_graph.test" in captured.err
    assert "hello" in captured.err


def test_setup_logging_is_idempotent(capsys: pytest.CaptureFixture[str]) -> None:
    setup_logging("INFO")
    setup_logging("INFO")
    assert len(logging.getLogger().handlers) == 1
    logging.getLogger("dup").warning("once")
    assert capsys.readouterr().err.count("once") == 1


def test_setup_logging_respects_level(capsys: pytest.CaptureFixture[str]) -> None:
    setup_logging("warning")
    logging.getLogger("lvl").info("hidden")
    logging.getLogger("lvl").error("shown")
    err = capsys.readouterr().err
    assert "hidden" not in err
    assert "shown" in err


def test_noisy_loggers_are_silenced() -> None:
    setup_logging("DEBUG")
    for name in NOISY_LOGGERS:
        assert logging.getLogger(name).level == logging.WARNING


def test_json_format_one_object_per_line(capsys: pytest.CaptureFixture[str]) -> None:
    setup_logging("DEBUG", fmt="json")
    log = logging.getLogger("research_graph.json")
    log.debug("первое сообщение", extra={"repo": "octo/cat"})
    log.info("второе %s", "сообщение")
    lines = capsys.readouterr().err.strip().splitlines()
    assert len(lines) == 2
    first, second = (json.loads(line) for line in lines)
    assert first["level"] == "DEBUG"
    assert first["logger"] == "research_graph.json"
    assert first["message"] == "первое сообщение"
    assert first["repo"] == "octo/cat"
    assert "ts" in first
    assert second["message"] == "второе сообщение"


def test_json_formatter_includes_exception() -> None:
    formatter = JsonFormatter()
    try:
        raise ValueError("boom")
    except ValueError:
        record = logging.getLogger("x").makeRecord(
            "x", logging.ERROR, __file__, 1, "failed", (), exc_info=sys.exc_info()
        )
    data = json.loads(formatter.format(record))
    assert data["message"] == "failed"
    assert "ValueError: boom" in data["exc_info"]
