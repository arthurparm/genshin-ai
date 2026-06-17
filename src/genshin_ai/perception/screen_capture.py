"""Real screen-capture backend isolated behind the CaptureSource protocol."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from types import TracebackType
from typing import Any, Self

from genshin_ai.perception.frame import CapturedFrame


class ScreenCaptureDependencyError(RuntimeError):
    """Raised when the optional screen-capture dependency is unavailable."""


class MssScreenCaptureSource:
    """Capture frames from the primary monitor using the optional mss backend."""

    source = "mss"

    def __init__(self, monitor_index: int = 1) -> None:
        self.monitor_index = monitor_index
        self._mss_module = _import_mss()
        self._screen_capture: Any | None = self._mss_module.mss()
        self._monitor: Any | None = None
        self._closed = False
        self._next_frame_id = 1

        try:
            monitors = self._screen_capture.monitors
            if monitor_index < 0 or monitor_index >= len(monitors):
                raise ValueError(
                    f"Monitor index {monitor_index} is not available. "
                    f"Detected {len(monitors) - 1} monitor(s)."
                )
            self._monitor = monitors[monitor_index]
        except Exception:
            self.close()
            raise

    def capture_frame(self) -> CapturedFrame:
        """Capture one frame from the configured monitor."""
        if self._closed or self._screen_capture is None or self._monitor is None:
            raise RuntimeError("Cannot capture frame after MssScreenCaptureSource has been closed.")

        screenshot = self._screen_capture.grab(self._monitor)

        frame_id = self._next_frame_id
        self._next_frame_id += 1

        return CapturedFrame(
            frame_id=frame_id,
            width=screenshot.width,
            height=screenshot.height,
            source=self.source,
            data=bytes(screenshot.raw),
        )

    def close(self) -> None:
        """Release the underlying mss capture resource."""
        if self._closed:
            return

        screen_capture = self._screen_capture
        self._screen_capture = None
        self._monitor = None
        self._closed = True

        if screen_capture is None:
            return

        close = getattr(screen_capture, "close", None)
        if callable(close):
            close()
            return

        exit_context = getattr(screen_capture, "__exit__", None)
        if callable(exit_context):
            exit_context(None, None, None)

    def __enter__(self) -> Self:
        """Return the active capture source for context-manager usage."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Release the capture resource when leaving a context manager."""
        self.close()


def save_frame_sample_ppm(frame: CapturedFrame, output_path: Path | str) -> Path:
    """Save a BGRA frame sample as a binary PPM image."""
    if frame.data is None:
        raise ValueError("Cannot save frame sample because frame.data is None.")

    expected_bgra_size = frame.width * frame.height * 4
    if len(frame.data) != expected_bgra_size:
        raise ValueError(
            "Cannot save frame sample because frame.data size does not match "
            f"BGRA dimensions: expected {expected_bgra_size}, got {len(frame.data)}."
        )

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    rgb_data = _bgra_to_rgb(frame.data)
    header = f"P6\n{frame.width} {frame.height}\n255\n".encode("ascii")

    with path.open("wb") as file:
        file.write(header)
        file.write(rgb_data)

    return path


def sample_frame_path(captures_dir: Path | str, frame: CapturedFrame) -> Path:
    """Build a deterministic sample filename containing the frame id."""
    return Path(captures_dir) / f"frame_{frame.frame_id:06d}.ppm"


def _bgra_to_rgb(data: bytes) -> bytes:
    rgb = bytearray()

    for index in range(0, len(data), 4):
        blue = data[index]
        green = data[index + 1]
        red = data[index + 2]
        rgb.extend((red, green, blue))

    return bytes(rgb)


def _import_mss() -> Any:
    try:
        return import_module("mss")
    except ImportError as error:
        raise ScreenCaptureDependencyError(
            "The optional screen-capture dependency 'mss' is not installed. "
            "Install it with 'pip install -e \".[capture]\"' or 'pip install mss'."
        ) from error
