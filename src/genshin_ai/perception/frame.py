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
