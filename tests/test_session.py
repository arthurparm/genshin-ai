import json
from pathlib import Path

from genshin_ai.core.config import AppConfig, RuntimePathsConfig
from genshin_ai.core.runtime import RuntimeContext
from genshin_ai.core.session import create_run_session


def test_create_run_session_creates_root_directory(tmp_path: Path) -> None:
    runtime = RuntimeContext(run_id="test-run")
    config = AppConfig(paths=RuntimePathsConfig(runs_dir=str(tmp_path / "runs")))

    session = create_run_session(runtime, config)

    assert session.root_dir == tmp_path / "runs" / "test-run"
    assert session.root_dir.exists()


def test_create_run_session_creates_artifact_directories(tmp_path: Path) -> None:
    runtime = RuntimeContext(run_id="test-run")
    config = AppConfig(paths=RuntimePathsConfig(runs_dir=str(tmp_path / "runs")))

    session = create_run_session(runtime, config)

    assert session.logs_dir.is_dir()
    assert session.captures_dir.is_dir()
    assert session.replays_dir.is_dir()
    assert session.artifacts_dir.is_dir()


def test_create_run_session_writes_metadata(tmp_path: Path) -> None:
    runtime = RuntimeContext(run_id="test-run")
    config = AppConfig(paths=RuntimePathsConfig(runs_dir=str(tmp_path / "runs")))

    session = create_run_session(runtime, config)

    assert session.metadata_path.exists()

    metadata = json.loads(session.metadata_path.read_text(encoding="utf-8"))

    assert metadata["run_id"] == "test-run"
    assert metadata["project_phase"] == runtime.project_phase
    assert metadata["paths"]["root_dir"] == str(tmp_path / "runs" / "test-run")
    assert metadata["paths"]["logs_dir"] == str(tmp_path / "runs" / "test-run" / "logs")
    assert metadata["paths"]["captures_dir"] == str(
        tmp_path / "runs" / "test-run" / "captures"
    )
    assert metadata["paths"]["replays_dir"] == str(tmp_path / "runs" / "test-run" / "replays")
    assert metadata["paths"]["artifacts_dir"] == str(
        tmp_path / "runs" / "test-run" / "artifacts"
    )
    assert metadata["config_summary"]["paths"]["runs_dir"] == str(tmp_path / "runs")


def test_create_run_session_uses_configured_runs_dir(tmp_path: Path) -> None:
    runtime = RuntimeContext(run_id="test-run")
    configured_runs_dir = tmp_path / "custom-runs"
    config = AppConfig(paths=RuntimePathsConfig(runs_dir=str(configured_runs_dir)))

    session = create_run_session(runtime, config)

    assert session.root_dir == configured_runs_dir / "test-run"
    assert session.metadata_path == configured_runs_dir / "test-run" / "metadata.json"
