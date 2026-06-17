import json
from pathlib import Path
from typing import NamedTuple

import pytest

from genshin_ai.core.config import AppConfig, RuntimePathsConfig
from genshin_ai.core.logging import JsonlEventLogger
from genshin_ai.core.runtime import RuntimeContext
from genshin_ai.core.session import RunSession, create_run_session
from genshin_ai.perception.benchmark import (
    CaptureBenchmarkReport,
    run_capture_benchmark,
    save_capture_benchmark_report,
)
from genshin_ai.perception.capture import MockCaptureSource
from genshin_ai.perception.frame import CapturedFrame


class BgraCaptureSource:
    source = "bgra-test"

    def __init__(self) -> None:
        self._next_frame_id = 1

    def capture_frame(self) -> CapturedFrame:
        frame_id = self._next_frame_id
        self._next_frame_id += 1
        return CapturedFrame(
            frame_id=frame_id,
            width=2,
            height=1,
            source=self.source,
            data=bytes((10, 20, 30, 255, 40, 50, 60, 255)),
        )


class BenchmarkContext(NamedTuple):
    runtime: RuntimeContext
    session: RunSession
    logger: JsonlEventLogger


def test_capture_benchmark_report_serializes_to_dict() -> None:
    report = CaptureBenchmarkReport(
        run_id="test-run",
        frames_requested=3,
        frames_captured=3,
        failed_frames=0,
        preprocess_enabled=False,
        source_width=1280,
        source_height=720,
        process_width=None,
        process_height=None,
        elapsed_seconds=1.0,
        actual_fps=3.0,
        average_capture_ms=1.0,
        average_preprocess_ms=0.0,
        average_total_frame_ms=1.2,
        samples_saved=0,
    )

    payload = report.to_dict()

    assert payload["run_id"] == "test-run"
    assert payload["frames_captured"] == 3
    assert payload["actual_fps"] == 3.0


def test_save_capture_benchmark_report_writes_json(tmp_path: Path) -> None:
    report = CaptureBenchmarkReport(
        run_id="test-run",
        frames_requested=1,
        frames_captured=1,
        failed_frames=0,
        preprocess_enabled=False,
        source_width=2,
        source_height=1,
        process_width=None,
        process_height=None,
        elapsed_seconds=0.1,
        actual_fps=10.0,
        average_capture_ms=1.0,
        average_preprocess_ms=0.0,
        average_total_frame_ms=1.0,
        samples_saved=0,
    )

    path = save_capture_benchmark_report(report, tmp_path / "report.json")

    assert path.exists()
    assert json.loads(path.read_text(encoding="utf-8"))["run_id"] == "test-run"


def test_run_capture_benchmark_without_preprocess(tmp_path: Path) -> None:
    runtime, session, logger = _benchmark_context(tmp_path)
    source = MockCaptureSource(width=1280, height=720)

    report = run_capture_benchmark(
        source=source,
        runtime=runtime,
        session=session,
        logger=logger,
        frames=3,
        preprocess=False,
        process_width=640,
        process_height=360,
        save_every=None,
    )

    assert report.run_id == runtime.run_id
    assert report.frames_requested == 3
    assert report.frames_captured == 3
    assert report.failed_frames == 0
    assert report.actual_fps > 0
    assert report.process_width is None
    assert report.process_height is None


def test_run_capture_benchmark_with_preprocess(tmp_path: Path) -> None:
    runtime, session, logger = _benchmark_context(tmp_path)

    report = run_capture_benchmark(
        source=BgraCaptureSource(),
        runtime=runtime,
        session=session,
        logger=logger,
        frames=2,
        preprocess=True,
        process_width=1,
        process_height=1,
        save_every=None,
    )

    assert report.frames_captured == 2
    assert report.failed_frames == 0
    assert report.preprocess_enabled is True
    assert report.source_width == 2
    assert report.source_height == 1
    assert report.process_width == 1
    assert report.process_height == 1
    assert report.average_preprocess_ms > 0


def test_run_capture_benchmark_rejects_invalid_arguments(tmp_path: Path) -> None:
    runtime, session, logger = _benchmark_context(tmp_path)

    with pytest.raises(ValueError, match="frames"):
        run_capture_benchmark(
            source=MockCaptureSource(width=1, height=1),
            runtime=runtime,
            session=session,
            logger=logger,
            frames=0,
            preprocess=False,
            process_width=1,
            process_height=1,
            save_every=None,
        )

    with pytest.raises(ValueError, match="save_every"):
        run_capture_benchmark(
            source=MockCaptureSource(width=1, height=1),
            runtime=runtime,
            session=session,
            logger=logger,
            frames=1,
            preprocess=False,
            process_width=1,
            process_height=1,
            save_every=0,
        )


def test_run_capture_benchmark_writes_events(tmp_path: Path) -> None:
    runtime, session, logger = _benchmark_context(tmp_path)

    run_capture_benchmark(
        source=MockCaptureSource(width=1280, height=720),
        runtime=runtime,
        session=session,
        logger=logger,
        frames=1,
        preprocess=False,
        process_width=640,
        process_height=360,
        save_every=None,
    )

    events = [
        json.loads(line)
        for line in (session.logs_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    event_names = [event["event"] for event in events]

    assert "capture_benchmark_started" in event_names
    assert "capture_benchmark_finished" in event_names


def test_run_capture_benchmark_saves_samples(tmp_path: Path) -> None:
    runtime, session, logger = _benchmark_context(tmp_path)

    report = run_capture_benchmark(
        source=BgraCaptureSource(),
        runtime=runtime,
        session=session,
        logger=logger,
        frames=2,
        preprocess=True,
        process_width=1,
        process_height=1,
        save_every=1,
    )

    samples = sorted(session.captures_dir.glob("processed_frame_*.ppm"))

    assert report.samples_saved == 2
    assert len(samples) == 2


def _benchmark_context(tmp_path: Path) -> BenchmarkContext:
    runtime = RuntimeContext(run_id="test-run")
    config = AppConfig(paths=RuntimePathsConfig(runs_dir=str(tmp_path / "runs")))
    session = create_run_session(runtime, config)
    logger = JsonlEventLogger(runtime=runtime, log_dir=session.logs_dir, filename="events.jsonl")
    return BenchmarkContext(runtime, session, logger)
