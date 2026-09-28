# research-graph

![CI](https://github.com/777werona-afk/research-graph/actions/workflows/ci.yml/badge.svg)

**research-graph** — учебный проект курса, который развивается в течение семестра:
инструмент для сбора данных об исследовательских репозиториях и публикациях
(GitHub API, снимки данных) и построения по ним графа связей
«репозиторий — автор — публикация». Данные проходят слои Bronze → Silver → Gold,
а результат доступен через CLI и (позже) HTTP API.

На текущем этапе (ЛР1) в репозитории развёрнут каркас: управление зависимостями
через `uv`, src-layout, конфигурация на `pydantic-settings`, логирование,
CLI `rg` на Typer, тесты, `ruff` + `mypy --strict`, pre-commit и GitHub Actions.

## Требования

- Python **3.12+** (uv поставит его сам, если нужного интерпретатора нет);
- [uv](https://docs.astral.sh/uv/) **0.8+**;
- git.

Установка uv:

```bash
# Linux / macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Установка

```bash
git clone https://github.com/777werona-afk/research-graph.git
cd research-graph
uv sync
```

`uv sync` создаёт `.venv`, ставит зависимости строго по `uv.lock` и сам пакет
(вместе с командой `rg`). Проверка:

```bash
uv run rg --help
```

## Конфигурация

Настройки читаются из переменных окружения с префиксом `RG_` и из файла `.env`
в текущей директории (переменные окружения важнее `.env`). Шаблон — `.env.example`:

```bash
cp .env.example .env
```

| Переменная            | Описание                                              | По умолчанию | Ограничения                          |
|-----------------------|-------------------------------------------------------|--------------|--------------------------------------|
| `RG_GITHUB_TOKEN`     | Персональный токен GitHub (в выводе всегда маскируется) | не задан     | пустая строка = не задан             |
| `RG_DATA_DIR`         | Корневая директория данных                           | `data`       | путь                                 |
| `RG_LOG_LEVEL`        | Уровень логирования                                   | `INFO`       | `DEBUG`/`INFO`/`WARNING`/`ERROR`/`CRITICAL`, регистр не важен |
| `RG_LOG_FORMAT`       | Формат логов                                          | `text`       | `text` или `json`                    |
| `RG_REQUEST_TIMEOUT`  | Таймаут HTTP-запросов, секунды                        | `10`         | `0 < x ≤ 300`                        |
| `RG_MAX_CONCURRENCY`  | Максимум одновременных запросов                       | `4`          | `1 … 64`                             |

Некорректное значение (например, `RG_MAX_CONCURRENCY=0`) приводит к ошибке
валидации: `rg check-config` завершится с кодом `2` и покажет, какое поле неверно.

## Использование

```bash
uv run rg --help
```

```text
 Usage: rg [OPTIONS] COMMAND [ARGS]...

 research-graph: инструменты для построения графа исследований.

╭─ Options ────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                      │
╰──────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────╮
│ version       Показать версию пакета.                            │
│ check-config  Загрузить настройки, включить логирование и        │
│               вывести сводку (без секретов).                     │
╰──────────────────────────────────────────────────────────────────╯
```

```bash
uv run rg version
```

```text
0.1.0
```

```bash
RG_GITHUB_TOKEN=ghp_supersecretvalue uv run rg check-config
```

```text
2026-09-28T17:00:00+0300 INFO     research_graph.cli: Конфигурация загружена
research-graph configuration:
  github_token     ghp_****alue
  data_dir         data
  log_level        INFO
  log_format       text
  request_timeout  10 s
  max_concurrency  4
```

Строка лога идёт в **stderr**, сводка — в **stdout**, поэтому
`uv run rg check-config 2>/dev/null` выводит только сводку.
Токен никогда не печатается целиком — только маска `ghp_****abcd`.

Логи в JSON (одна запись — одна строка):

```bash
RG_LOG_FORMAT=json uv run rg check-config
```

```text
{"ts": "2026-09-28T14:00:00+00:00", "level": "INFO", "logger": "research_graph.cli", "message": "Конфигурация загружена"}
research-graph configuration:
  ...
```

Флаг `--create-dirs` создаёт `data_dir`, если её ещё нет:

```bash
uv run rg check-config --create-dirs
```

## Разработка

```bash
uv run ruff check .            # линтер
uv run ruff format --check .   # проверка форматирования (без --check — отформатировать)
uv run mypy                    # типы, strict-режим, src + tests
uv run pytest                  # тесты + покрытие (порог 90 %)
```

pre-commit (ruff, ruff-format, mypy и базовые проверки файлов):

```bash
uv run pre-commit install          # один раз после клонирования
uv run pre-commit run --all-files  # прогнать по всему репозиторию
```

Хуки ruff и mypy запускаются через `uv run`, т.е. из окружения проекта: их версии
совпадают с `uv.lock`, а mypy видит pydantic и его плагин.

CI (`.github/workflows/ci.yml`) на каждый push и pull request запускает
линтер, проверку форматирования, mypy и pre-commit, а тесты — в матрице
Ubuntu / Windows × Python 3.12 / 3.13.

## Структура проекта

```text
research-graph/
├── .github/workflows/ci.yml   # CI: lint, format, mypy, pre-commit, тесты (матрица ОС × Python)
├── docs/
│   └── lab1_report.md         # отчёт по ЛР1
├── src/research_graph/        # пакет (src-layout)
│   ├── __init__.py            # __version__ из метаданных пакета
│   ├── __main__.py            # python -m research_graph
│   ├── cli.py                 # Typer-приложение `rg`: version, check-config
│   ├── config.py              # Settings (pydantic-settings, префикс RG_, .env)
│   ├── logging_setup.py       # setup_logging(): stderr, text/JSON
│   ├── py.typed               # маркер PEP 561
│   ├── api/                   # HTTP API (следующие ЛР)
│   ├── models/                # доменные модели (ЛР2)
│   ├── pipelines/             # пайплайны обработки (следующие ЛР)
│   ├── sources/               # источники данных: GitHub API, снимки (ЛР2)
│   └── storage/               # хранилище Bronze/Silver/Gold (ЛР3)
├── tests/
│   ├── conftest.py            # изоляция от .env и RG_* переменных
│   ├── test_cli.py
│   ├── test_config.py
│   └── test_logging.py
├── .env.example               # шаблон конфигурации (без секретов)
├── .pre-commit-config.yaml
├── .python-version            # 3.12
├── pyproject.toml             # метаданные, зависимости, настройки ruff/mypy/pytest/coverage
└── uv.lock                    # зафиксированные версии зависимостей
```
