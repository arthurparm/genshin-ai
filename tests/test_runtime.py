from datetime import UTC, datetime

from genshin_ai.core.runtime import RuntimeContext


def test_runtime_context_has_run_id() -> None:
    runtime = RuntimeContext()

    assert runtime.run_id
    assert isinstance(runtime.started_at_utc, datetime)
    assert runtime.started_at_utc.tzinfo == UTC


def test_runtime_context_serializes_to_dict() -> None:
    runtime = RuntimeContext(run_id="test-run")

    payload = runtime.to_dict()

    assert payload["run_id"] == "test-run"
    assert payload["project_phase"] == "FASE 0.3 - Run Session and Artifact Directories"
    assert "started_at_utc" in payload
