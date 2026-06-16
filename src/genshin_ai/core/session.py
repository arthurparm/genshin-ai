"""Run session directories and metadata for runtime artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from genshin_ai.core.config import AppConfig
from genshin_ai.core.runtime import RuntimeContext


@dataclass(frozen=True)
class RunSession:
    """Filesystem layout for one agent execution."""

    run_id: str
    root_dir: Path
    logs_dir: Path
    captures_dir: Path
    replays_dir: Path
    artifacts_dir: Path
    metadata_path: Path

    def to_dict(self) -> dict[str, str]:
        """Serialize session paths into JSON-compatible strings."""
        return {
            "run_id": self.run_id,
            "root_dir": str(self.root_dir),
            "logs_dir": str(self.logs_dir),
            "captures_dir": str(self.captures_dir),
            "replays_dir": str(self.replays_dir),
            "artifacts_dir": str(self.artifacts_dir),
            "metadata_path": str(self.metadata_path),
        }


def create_run_session(runtime: RuntimeContext, config: AppConfig) -> RunSession:
    """Create a run-scoped artifact directory tree and metadata file."""
    root_dir = Path(config.paths.runs_dir) / runtime.run_id
    session = RunSession(
        run_id=runtime.run_id,
        root_dir=root_dir,
        logs_dir=root_dir / "logs",
        captures_dir=root_dir / "captures",
        replays_dir=root_dir / "replays",
        artifacts_dir=root_dir / "artifacts",
        metadata_path=root_dir / "metadata.json",
    )

    _create_session_directories(session)
    _write_metadata(runtime, config, session)

    return session


def _create_session_directories(session: RunSession) -> None:
    for directory in (
        session.root_dir,
        session.logs_dir,
        session.captures_dir,
        session.replays_dir,
        session.artifacts_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)


def _write_metadata(runtime: RuntimeContext, config: AppConfig, session: RunSession) -> None:
    metadata = _build_metadata(runtime, config, session)
    session.metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _build_metadata(
    runtime: RuntimeContext,
    config: AppConfig,
    session: RunSession,
) -> dict[str, Any]:
    return {
        "run_id": runtime.run_id,
        "project_phase": runtime.project_phase,
        "started_at_utc": runtime.started_at_utc.isoformat(),
        "created_at_utc": datetime.now(UTC).isoformat(),
        "paths": session.to_dict(),
        "config_summary": config.to_dict(),
    }
