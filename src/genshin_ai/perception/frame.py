"""Frame models for capture and perception pipelines."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class CapturedFrame:
    """A frame captured from a source.

    The raw payload is optional so the capture contract can be tested before any
    real screen-capture backend exists.
    """

    frame_id: int
    width: int
    height: int
    captured_at_utc: datetime = field(default_factory=lambda: datetime.now(UTC))
    source: str = "unknown"
    data: bytes | None = None

    def metadata(self) -> dict[str, str | int]:
        """Return JSON-compatible frame metadata without raw frame bytes."""
        return {
            "frame_id": self.frame_id,
            "width": self.width,
            "height": self.height,
            "captured_at_utc": self.captured_at_utc.isoformat(),
            "source": self.source,
        }


@dataclass(frozen=True)
class ProcessedFrame:
    """A preprocessed RGB frame derived from a captured frame."""

    frame_id: int
    width: int
    height: int
    source_frame_width: int
    source_frame_height: int
    data: bytes
    processed_at_utc: datetime = field(default_factory=lambda: datetime.now(UTC))
    source: str = "preprocess"
    pixel_format: str = "RGB"

    def metadata(self) -> dict[str, str | int]:
        """Return JSON-compatible processed frame metadata without raw bytes."""
        return {
            "frame_id": self.frame_id,
            "width": self.width,
            "height": self.height,
            "source_frame_width": self.source_frame_width,
            "source_frame_height": self.source_frame_height,
            "processed_at_utc": self.processed_at_utc.isoformat(),
            "source": self.source,
            "pixel_format": self.pixel_format,
        }
