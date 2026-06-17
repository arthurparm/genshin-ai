from pathlib import Path

import pytest

from genshin_ai.core.config import (
    CaptureConfig,
    ModelRoutingConfig,
    load_config,
)


def test_load_config_without_path_returns_safe_defaults() -> None:
    config = load_config()

    assert config.logging.log_dir == "logs"
    assert config.logging.level == "INFO"
    assert config.paths.runs_dir == "runs"
    assert config.capture == CaptureConfig()
    assert config.model_routing == ModelRoutingConfig()


def test_capture_config_defaults_are_safe() -> None:
    capture = CaptureConfig()

    assert capture.enabled is False
    assert capture.target_fps == 10
    assert capture.process_width == 1280
    assert capture.process_height == 720
    assert capture.preprocess_backend == "python"
    assert capture.save_sample_frames is False


def test_model_routing_is_disabled_by_default() -> None:
    config = load_config()

    assert config.model_routing.enabled is False


def test_load_config_from_valid_toml(tmp_path: Path) -> None:
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        """
[logging]
log_dir = "custom-logs"
level = "DEBUG"

[capture]
enabled = true
target_fps = 15
process_width = 960
process_height = 540
preprocess_backend = "pillow"
save_sample_frames = true

[model_routing]
enabled = true
provider = "omnirouter"
planner_model = "planner-test"
""".strip(),
        encoding="utf-8",
    )

    config = load_config(config_file)

    assert config.logging.log_dir == "custom-logs"
    assert config.logging.level == "DEBUG"
    assert config.capture.enabled is True
    assert config.capture.target_fps == 15
    assert config.capture.process_width == 960
    assert config.capture.process_height == 540
    assert config.capture.preprocess_backend == "pillow"
    assert config.capture.save_sample_frames is True
    assert config.model_routing.enabled is True
    assert config.model_routing.provider == "omnirouter"
    assert config.model_routing.planner_model == "planner-test"


def test_partial_section_override_preserves_defaults(tmp_path: Path) -> None:
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        """
[capture]
target_fps = 20
""".strip(),
        encoding="utf-8",
    )

    config = load_config(config_file)

    assert config.capture.enabled is False
    assert config.capture.target_fps == 20
    assert config.capture.process_width == 1280
    assert config.capture.process_height == 720
    assert config.capture.preprocess_backend == "python"
    assert config.capture.save_sample_frames is False
    assert config.logging.log_dir == "logs"


def test_missing_config_file_raises_file_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        load_config("missing-config.toml")


def test_unknown_key_in_known_section_raises_value_error(tmp_path: Path) -> None:
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        """
[capture]
unknown_key = true
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unknown config key"):
        load_config(config_file)


def test_unknown_section_raises_value_error(tmp_path: Path) -> None:
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        """
[unknown]
enabled = true
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unknown config section"):
        load_config(config_file)


def test_config_serializes_to_dict() -> None:
    config = load_config()

    payload = config.to_dict()

    assert payload["logging"] == {"log_dir": "logs", "level": "INFO"}
    assert payload["capture"] == {
        "enabled": False,
        "target_fps": 10,
        "process_width": 1280,
        "process_height": 720,
        "preprocess_backend": "python",
        "save_sample_frames": False,
    }
