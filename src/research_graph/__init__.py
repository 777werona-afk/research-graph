"""research-graph: сбор и анализ графа научных публикаций и репозиториев."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("research-graph")
except PackageNotFoundError:  # pragma: no cover - пакет не установлен
    __version__ = "0.0.0"

__all__ = ["__version__"]
