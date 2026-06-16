import json
from pathlib import Path

from genshin_ai.core.logging import JsonlEventLogger, LogEvent
from genshin_ai.core.runtime import RuntimeContext


def test_jsonl_event_logger_writes_event(tmp_path: Path) -> None:
    runtime = RuntimeContext(run_id="test-run")
    logger = JsonlEventLogger(runtime=runtime, log_dir=tmp_path, filename="test.jsonl")

    payload = logger.emit(
        LogEvent(
            event="test_event",
            module="tests",
            message="Test event emitted.",
            data={"ok": True},
        )
    )

    log_file = tmp_path / "test.jsonl"

    assert log_file.exists()
    assert payload["event"] == "test_event"
    assert payload["module"] == "tests"
    assert payload["runtime"]["run_id"] == "test-run"

    lines = log_file.read_text(encoding="utf-8").splitlines()

    assert len(lines) == 1

    parsed = json.loads(lines[0])

    assert parsed["event"] == "test_event"
    assert parsed["module"] == "tests"
    assert parsed["data"]["ok"] is True
    assert parsed["runtime"]["run_id"] == "test-run"


def test_log_event_without_message_serializes_without_message_key() -> None:
    runtime = RuntimeContext(run_id="test-run")

    event = LogEvent(
        event="no_message_event",
        module="tests",
    )

    payload = event.to_dict(runtime)

    assert payload["event"] == "no_message_event"
    assert payload["module"] == "tests"
    assert "message" not in payload
