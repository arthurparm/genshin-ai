"""Runtime metadata used across one agent execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4


@dataclass(frozen=True)
class RuntimeContext:
    """Immutable metadata for a single runtime session.

    RuntimeContext identifies one execution of the system. It is intentionally
    independent from screen capture, OCR, computer vision, LLMs, and execution.
    """

    run_id: str = field(default_factory=lambda: str(uuid4()))
    project_phase: str = "FASE 0.2 - Typed Configuration"
    started_at_utc: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, str]:
        """Serialize runtime metadata into JSON-compatible values."""
        return {
            "run_id": self.run_id,
            "project_phase": self.project_phase,
            "started_at_utc": self.started_at_utc.isoformat(),
        }
