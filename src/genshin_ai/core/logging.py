"""Structured JSONL logging for the Genshin AI research agent."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from genshin_ai.core.runtime import RuntimeContext

JsonValue = str | int | float | bool | None | dict[str, Any] | list[Any]


@dataclass(frozen=True)
class LogEvent:
    """A structured event emitted by a project module."""

    event: str
    module: str
    level: str = "INFO"
    message: str | None = None
    data: dict[str, JsonValue] = field(default_factory=dict)
    timestamp_utc: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self, runtime: RuntimeContext) -> dict[str, Any]:
        """Serialize the event with runtime metadata."""
        payload: dict[str, Any] = {
            "timestamp_utc": self.timestamp_utc.isoformat(),
            "level": self.level,
            "event": self.event,
            "module": self.module,
            "runtime": runtime.to_dict(),
            "data": self.data,
        }

        if self.message is not None:
            payload["message"] = self.message

        return payload


class JsonlEventLogger:
    """Append-only JSONL event logger.

    One JSON object is written per line. This format is intentionally simple so
    future replay, metrics, and failure-analysis modules can consume it.
    """

    def __init__(
        self,
        runtime: RuntimeContext,
        log_dir: Path | str = "logs",
        filename: str | None = None,
    ) -> None:
        self.runtime = runtime
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        safe_filename = filename or f"{runtime.run_id}.jsonl"
        self.file_path = self.log_dir / safe_filename

    def emit(self, event: LogEvent) -> dict[str, Any]:
        """Write one structured event and return its serialized payload."""
        payload = event.to_dict(self.runtime)

        with self.file_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
            file.write("\n")

        return payload


def configure_console_logging(level: int = logging.INFO) -> None:
    """Configure human-readable console logging."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def get_logger(name: str) -> logging.Logger:
    """Return a standard Python logger."""
    return logging.getLogger(name)
