"""Operational capture benchmark reporting."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from genshin_ai.core.logging import JsonlEventLogger, JsonValue, LogEvent
from genshin_ai.core.runtime import RuntimeContext
from genshin_ai.core.session import RunSession
from genshin_ai.perception.capture import CaptureSource
from genshin_ai.perception.frame import CapturedFrame, ProcessedFrame
from genshin_ai.perception.preprocess import (
    preprocess_bgra_frame,
    processed_frame_sample_path,
    save_processed_frame_sample_ppm,
)
from genshin_ai.perception.screen_capture import (
    sample_frame_path,
    save_frame_sample_ppm,
)


@dataclass(frozen=True)
class CaptureBenchmarkReport:
    """Summary report for a capture benchmark run."""

    run_id: str
    frames_requested: int
    frames_captured: int
    failed_frames: int
    preprocess_enabled: bool
    source_width: int | None
    source_height: int | None
    process_width: int | None
    process_height: int | None
    elapsed_seconds: float
    actual_fps: float
    average_capture_ms: float
    average_preprocess_ms: float
    average_total_frame_ms: float
    samples_saved: int

    def to_dict(self) -> dict[str, str | int | float | bool | None]:
        """Serialize the benchmark report into JSON-compatible values."""
        return asdict(self)


def save_capture_benchmark_report(
    report: CaptureBenchmarkReport,
    path: Path | str,
) -> Path:
    """Save a capture benchmark report as indented JSON."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return output_path


def run_capture_benchmark(
    source: CaptureSource,
    runtime: RuntimeContext,
    session: RunSession,
    logger: JsonlEventLogger,
    frames: int,
    preprocess: bool,
    process_width: int,
    process_height: int,
    save_every: int | None,
) -> CaptureBenchmarkReport:
    """Run an operational capture benchmark and return a report."""
    if frames <= 0:
        raise ValueError("frames must be positive")
    if save_every is not None and save_every <= 0:
        raise ValueError("save_every must be positive when provided")

    logger.emit(
        LogEvent(
            event="capture_benchmark_started",
            module="perception.benchmark",
            data={
                "frames": frames,
                "preprocess": preprocess,
                "process_width": process_width,
                "process_height": process_height,
                "save_every": save_every,
            },
        )
    )

    benchmark_started = time.perf_counter()
    frames_captured = 0
    failed_frames = 0
    samples_saved = 0
    source_width: int | None = None
    source_height: int | None = None
    capture_durations_ms: list[float] = []
    preprocess_durations_ms: list[float] = []
    total_frame_durations_ms: list[float] = []

    for frame_index in range(1, frames + 1):
        frame_started = time.perf_counter()
        capture_ms = 0.0
        preprocess_ms = 0.0
        frame: CapturedFrame | None = None
        processed_frame: ProcessedFrame | None = None
        error_message: str | None = None

        try:
            capture_started = time.perf_counter()
            frame = source.capture_frame()
            capture_ms = _elapsed_ms(capture_started)
            capture_durations_ms.append(capture_ms)
            frames_captured += 1

            source_width = frame.width
            source_height = frame.height

            if preprocess:
                preprocess_started = time.perf_counter()
                processed_frame = preprocess_bgra_frame(
                    frame,
                    target_width=process_width,
                    target_height=process_height,
                )
                preprocess_ms = _elapsed_ms(preprocess_started)
                preprocess_durations_ms.append(preprocess_ms)

            if save_every is not None and frame_index % save_every == 0:
                if preprocess:
                    if processed_frame is None:
                        raise RuntimeError("processed_frame is missing for sample save")
                    output_path = save_processed_frame_sample_ppm(
                        processed_frame,
                        processed_frame_sample_path(session.captures_dir, processed_frame),
                    )
                else:
                    output_path = save_frame_sample_ppm(
                        frame,
                        sample_frame_path(session.captures_dir, frame),
                    )
                samples_saved += 1
                logger.emit(
                    LogEvent(
                        event="capture_benchmark_sample_saved",
                        module="perception.benchmark",
                        data={
                            "frame_index": frame_index,
                            "path": str(output_path),
                            "preprocess": preprocess,
                        },
                    )
                )
        except Exception as error:
            failed_frames += 1
            error_message = str(error)

        total_frame_ms = _elapsed_ms(frame_started)
        total_frame_durations_ms.append(total_frame_ms)
        logger.emit(
            LogEvent(
                event="capture_benchmark_frame",
                module="perception.benchmark",
                level="ERROR" if error_message is not None else "INFO",
                message=error_message,
                data={
                    "frame_index": frame_index,
                    "captured": frame is not None,
                    "preprocessed": processed_frame is not None,
                    "capture_ms": capture_ms,
                    "preprocess_ms": preprocess_ms,
                    "total_frame_ms": total_frame_ms,
                },
            )
        )

    elapsed_seconds = time.perf_counter() - benchmark_started
    report = CaptureBenchmarkReport(
        run_id=runtime.run_id,
        frames_requested=frames,
        frames_captured=frames_captured,
        failed_frames=failed_frames,
        preprocess_enabled=preprocess,
        source_width=source_width,
        source_height=source_height,
        process_width=process_width if preprocess else None,
        process_height=process_height if preprocess else None,
        elapsed_seconds=elapsed_seconds,
        actual_fps=frames_captured / elapsed_seconds if elapsed_seconds > 0 else 0.0,
        average_capture_ms=_average(capture_durations_ms),
        average_preprocess_ms=_average(preprocess_durations_ms),
        average_total_frame_ms=_average(total_frame_durations_ms),
        samples_saved=samples_saved,
    )

    logger.emit(
        LogEvent(
            event="capture_benchmark_finished",
            module="perception.benchmark",
            data=dict[str, JsonValue](report.to_dict()),
        )
    )

    return report


def _elapsed_ms(started: float) -> float:
    return (time.perf_counter() - started) * 1000.0


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)
