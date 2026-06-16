"""Capture metrics and smoke-test loop."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass

from genshin_ai.core.logging import JsonlEventLogger, JsonValue, LogEvent
from genshin_ai.perception.capture import CaptureSource


@dataclass(frozen=True)
class CaptureMetrics:
    """Summary metrics for a capture smoke test."""

    frames_captured: int
    target_fps: int
    elapsed_seconds: float
    actual_fps: float
    failed_frames: int

    def to_dict(self) -> dict[str, int | float]:
        """Serialize metrics into JSON-compatible values."""
        return asdict(self)


def run_capture_smoke_test(
    source: CaptureSource,
    logger: JsonlEventLogger,
    frame_count: int = 5,
    target_fps: int = 10,
) -> CaptureMetrics:
    """Run a bounded mock capture loop and emit structured events."""
    if frame_count < 0:
        raise ValueError("frame_count must be non-negative")
    if target_fps <= 0:
        raise ValueError("target_fps must be positive")

    logger.emit(
        LogEvent(
            event="capture_smoke_started",
            module="perception.capture",
            data={
                "frame_count": frame_count,
                "target_fps": target_fps,
            },
        )
    )

    started = time.perf_counter()
    frame_interval_seconds = 1.0 / target_fps
    frames_captured = 0
    failed_frames = 0

    for _ in range(frame_count):
        frame_started = time.perf_counter()

        try:
            frame = source.capture_frame()
            frames_captured += 1
            logger.emit(
                LogEvent(
                    event="capture_frame_captured",
                    module="perception.capture",
                    data=dict[str, JsonValue](frame.metadata()),
                )
            )
        except Exception as error:
            failed_frames += 1
            logger.emit(
                LogEvent(
                    event="capture_frame_failed",
                    module="perception.capture",
                    level="ERROR",
                    message=str(error),
                )
            )

        elapsed_for_frame = time.perf_counter() - frame_started
        time.sleep(max(0.0, frame_interval_seconds - elapsed_for_frame))

    elapsed_seconds = time.perf_counter() - started
    actual_fps = frames_captured / elapsed_seconds if elapsed_seconds > 0 else 0.0
    metrics = CaptureMetrics(
        frames_captured=frames_captured,
        target_fps=target_fps,
        elapsed_seconds=elapsed_seconds,
        actual_fps=actual_fps,
        failed_frames=failed_frames,
    )

    logger.emit(
        LogEvent(
            event="capture_smoke_finished",
            module="perception.capture",
            data=dict[str, JsonValue](metrics.to_dict()),
        )
    )

    return metrics
