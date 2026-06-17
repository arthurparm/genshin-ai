"""Typed application configuration for the Genshin AI research agent."""

from __future__ import annotations

import tomllib
from dataclasses import asdict, dataclass, fields, replace
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LoggingConfig:
    """Configuration for structured runtime logs."""

    log_dir: str = "logs"
    level: str = "INFO"

    def to_dict(self) -> dict[str, object]:
        """Serialize the config into JSON-compatible values."""
        return asdict(self)


@dataclass(frozen=True)
class RuntimePathsConfig:
    """Configuration for local runtime output directories."""

    runs_dir: str = "runs"
    captures_dir: str = "captures"
    replays_dir: str = "replays"
    artifacts_dir: str = "artifacts"

    def to_dict(self) -> dict[str, object]:
        """Serialize the config into JSON-compatible values."""
        return asdict(self)


@dataclass(frozen=True)
class CaptureConfig:
    """Configuration for future screen capture modules.

    Capture is disabled by default and is not implemented in FASE 0.2.
    """

    enabled: bool = False
    target_fps: int = 10
    process_width: int = 1280
    process_height: int = 720
    preprocess_backend: str = "python"
    save_sample_frames: bool = False

    def to_dict(self) -> dict[str, object]:
        """Serialize the config into JSON-compatible values."""
        return asdict(self)


@dataclass(frozen=True)
class ModelRoutingConfig:
    """Configuration for future model routing modules.

    Model routing is disabled by default and is not integrated in FASE 0.2.
    """

    enabled: bool = False
    provider: str = "none"
    planner_model: str = "none"

    def to_dict(self) -> dict[str, object]:
        """Serialize the config into JSON-compatible values."""
        return asdict(self)


@dataclass(frozen=True)
class AppConfig:
    """Root application configuration."""

    logging: LoggingConfig = LoggingConfig()
    paths: RuntimePathsConfig = RuntimePathsConfig()
    capture: CaptureConfig = CaptureConfig()
    model_routing: ModelRoutingConfig = ModelRoutingConfig()

    @classmethod
    def default(cls) -> AppConfig:
        """Return safe default configuration."""
        return cls()

    def to_dict(self) -> dict[str, object]:
        """Serialize the config into JSON-compatible values."""
        return {
            "logging": self.logging.to_dict(),
            "paths": self.paths.to_dict(),
            "capture": self.capture.to_dict(),
            "model_routing": self.model_routing.to_dict(),
        }


_SECTION_TYPES = {
    "logging": LoggingConfig,
    "paths": RuntimePathsConfig,
    "capture": CaptureConfig,
    "model_routing": ModelRoutingConfig,
}


def load_config(path: Path | str | None = None) -> AppConfig:
    """Load application configuration from TOML or return safe defaults."""
    config = AppConfig.default()

    if path is None:
        return config

    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(config_path)

    with config_path.open("rb") as file:
        raw_config = tomllib.load(file)

    _validate_sections(raw_config)

    for section_name, section_values in raw_config.items():
        if not isinstance(section_values, dict):
            raise ValueError(f"Config section '{section_name}' must be a table.")

        _validate_section_keys(section_name, section_values)
        current_section = getattr(config, section_name)
        updated_section = replace(current_section, **section_values)
        config = replace(config, **{section_name: updated_section})

    return config


def _validate_sections(raw_config: dict[str, Any]) -> None:
    unknown_sections = set(raw_config) - set(_SECTION_TYPES)
    if unknown_sections:
        unknown = ", ".join(sorted(unknown_sections))
        raise ValueError(f"Unknown config section(s): {unknown}")


def _validate_section_keys(section_name: str, section_values: dict[str, Any]) -> None:
    section_type = _SECTION_TYPES[section_name]
    known_keys = {field.name for field in fields(section_type)}
    unknown_keys = set(section_values) - known_keys

    if unknown_keys:
        unknown = ", ".join(sorted(unknown_keys))
        raise ValueError(f"Unknown config key(s) in section '{section_name}': {unknown}")
