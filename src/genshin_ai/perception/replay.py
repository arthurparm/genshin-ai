"""Replay sources for deterministic perception input."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from genshin_ai.perception.frame import ProcessedFrame


class ReplayFrameError(RuntimeError):
    """Raised when replay frames cannot be loaded or parsed."""


class ReplayEndOfSequenceError(ReplayFrameError):
    """Raised when a replay source has no more frames to load."""


@dataclass(frozen=True)
class ReplayLoadedFrame:
    """A replay frame loaded with its source path for auditability."""

    frame: ProcessedFrame
    path: Path


class ProcessedFrameReplaySource:
    """Load processed RGB frames from binary PPM files in deterministic order."""

    source = "replay.ppm"

    def __init__(self, frames_dir: Path | str) -> None:
        self.frames_dir = Path(frames_dir)
        if not self.frames_dir.is_dir():
            raise ReplayFrameError(f"Replay frames directory does not exist: {self.frames_dir}")

        self._frame_paths = sorted(self.frames_dir.glob("*.ppm"))
        if not self._frame_paths:
            raise ReplayFrameError(f"No .ppm replay frames found in directory: {self.frames_dir}")

        self._next_index = 0
        self._next_frame_id = 1

    def load_next_frame(self) -> ProcessedFrame:
        """Load the next replay frame from disk."""
        return self.load_next().frame

    def load_next(self) -> ReplayLoadedFrame:
        """Load the next replay frame and return its source path."""
        if self._next_index >= len(self._frame_paths):
            raise ReplayEndOfSequenceError("No more replay frames are available.")

        path = self._frame_paths[self._next_index]
        width, height, payload = _read_ppm_p6(path)

        frame_id = self._next_frame_id

        self._next_index += 1
        self._next_frame_id += 1

        return ReplayLoadedFrame(
            frame=ProcessedFrame(
                frame_id=frame_id,
                width=width,
                height=height,
                source_frame_width=width,
                source_frame_height=height,
                source=self.source,
                pixel_format="RGB",
                data=payload,
            ),
            path=path,
        )


def _read_ppm_p6(path: Path) -> tuple[int, int, bytes]:
    try:
        data = path.read_bytes()
    except OSError as error:
        raise ReplayFrameError(f"Failed to read replay frame file {path}: {error}") from error

    cursor = 0

    magic, cursor = _read_ascii_token(data, cursor, path)
    if magic != "P6":
        raise ReplayFrameError(f"Invalid PPM magic in {path}: expected P6, got {magic!r}.")

    width_text, cursor = _read_ascii_token(data, cursor, path)
    height_text, cursor = _read_ascii_token(data, cursor, path)
    max_value_text, cursor = _read_ascii_token(data, cursor, path)

    width = _parse_positive_int(width_text, "width", path)
    height = _parse_positive_int(height_text, "height", path)
    max_value = _parse_positive_int(max_value_text, "max value", path)
    if max_value != 255:
        raise ReplayFrameError(
            f"Unsupported PPM max value in {path}: expected 255, got {max_value}."
        )

    cursor = _consume_single_payload_separator(data, cursor, path)
    expected_size = width * height * 3
    payload = data[cursor:]
    if len(payload) != expected_size:
        raise ReplayFrameError(
            f"Invalid PPM RGB payload size in {path}: expected {expected_size}, got {len(payload)}."
        )

    return width, height, payload


def _read_ascii_token(data: bytes, cursor: int, path: Path) -> tuple[str, int]:
    cursor = _skip_ascii_whitespace(data, cursor)
    if cursor >= len(data):
        raise ReplayFrameError(f"Invalid PPM header in {path}: missing token.")

    start = cursor
    while cursor < len(data) and data[cursor] not in b" \t\r\n":
        cursor += 1

    try:
        token = data[start:cursor].decode("ascii")
    except UnicodeDecodeError as error:
        raise ReplayFrameError(f"Invalid PPM header in {path}: non-ASCII token.") from error

    return token, cursor


def _skip_ascii_whitespace(data: bytes, cursor: int) -> int:
    while cursor < len(data) and data[cursor] in b" \t\r\n":
        cursor += 1
    return cursor


def _consume_single_payload_separator(data: bytes, cursor: int, path: Path) -> int:
    if cursor >= len(data) or data[cursor] not in b" \t\r\n":
        raise ReplayFrameError(f"Invalid PPM header in {path}: missing payload separator.")
    return cursor + 1


def _parse_positive_int(value: str, field_name: str, path: Path) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise ReplayFrameError(f"Invalid PPM {field_name} in {path}: {value!r}.") from error

    if parsed <= 0:
        raise ReplayFrameError(f"Invalid PPM {field_name} in {path}: must be positive.")

    return parsed
