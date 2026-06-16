import json
from pathlib import Path

from genshin_ai.core.logging import JsonlEventLogger
from genshin_ai.core.runtime import RuntimeContext
from genshin_ai.perception.capture import MockCaptureSource
from genshin_ai.perception.metrics import run_capture_smoke_test


def test_run_capture_smoke_test_captures_expected_frame_count(tmp_path: Path) -> None:
    runtime = RuntimeContext(run_id="test-run")
    logger = JsonlEventLogger(runtime=runtime, log_dir=tmp_path, filename="events.jsonl")
    source = MockCaptureSource(width=1280, height=720)

    metrics = run_capture_smoke_test(
        source=source,
        logger=logger,
        frame_count=3,
        target_fps=1000,
    )

    assert metrics.frames_captured == 3
    assert metrics.failed_frames == 0
    assert metrics.target_fps == 1000
    assert metrics.actual_fps > 0


def test_run_capture_smoke_test_writes_capture_events(tmp_path: Path) -> None:
    runtime = RuntimeContext(run_id="test-run")
    logger = JsonlEventLogger(runtime=runtime, log_dir=tmp_path, filename="events.jsonl")
    source = MockCaptureSource(width=960, height=540)

    run_capture_smoke_test(
        source=source,
        logger=logger,
        frame_count=2,
        target_fps=1000,
    )

    log_file = tmp_path / "events.jsonl"
    events = [
        json.loads(line)
        for line in log_file.read_text(encoding="utf-8").splitlines()
    ]

    event_names = [event["event"] for event in events]

    assert event_names == [
        "capture_smoke_started",
        "capture_frame_captured",
        "capture_frame_captured",
        "capture_smoke_finished",
    ]
    assert events[1]["data"]["width"] == 960
    assert events[1]["data"]["height"] == 540
    assert events[-1]["data"]["frames_captured"] == 2
    assert events[-1]["data"]["actual_fps"] > 0
