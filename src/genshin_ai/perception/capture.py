"""Capture source abstractions and mock implementations."""

from __future__ import annotations

from typing import Protocol

from genshin_ai.perception.frame import CapturedFrame


class CaptureSource(Protocol):
    """Source capable of returning one captured frame."""

    def capture_frame(self) -> CapturedFrame:
        """Capture and return one frame."""
        ...


class MockCaptureSource:
    """Deterministic mock capture source for tests and smoke checks."""

    source = "mock"

    def __init__(self, width: int, height: int, include_fake_data: bool = False) -> None:
        self.width = width
        self.height = height
        self.include_fake_data = include_fake_data
        self._next_frame_id = 1

    def capture_frame(self) -> CapturedFrame:
        """Return a synthetic frame without touching the screen."""
        frame_id = self._next_frame_id
        self._next_frame_id += 1

        return CapturedFrame(
            frame_id=frame_id,
            width=self.width,
            height=self.height,
            source=self.source,
            data=self._fake_data() if self.include_fake_data else None,
        )

    def _fake_data(self) -> bytes:
        return f"mock-frame:{self._next_frame_id}".encode("ascii")
