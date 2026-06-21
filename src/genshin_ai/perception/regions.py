"""Region-of-interest extraction for processed RGB frames."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from genshin_ai.perception.frame import ProcessedFrame

if TYPE_CHECKING:
    from genshin_ai.core.config import RegionConfig

_SAFE_REGION_NAME = re.compile(r"^[A-Za-z0-9_-]+$")


class RegionExtractionError(RuntimeError):
    """Raised when an RGB region cannot be extracted or saved."""


@dataclass(frozen=True)
class RegionSpec:
    """Immutable region-of-interest coordinates in processed-frame space."""

    name: str
    x: int
    y: int
    width: int
    height: int

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Region name must not be empty.")
        if not _SAFE_REGION_NAME.fullmatch(self.name):
            raise ValueError(
                "Region name must contain only letters, numbers, underscores, or hyphens."
            )
        if self.x < 0:
            raise ValueError("Region x must be non-negative.")
        if self.y < 0:
            raise ValueError("Region y must be non-negative.")
        if self.width <= 0:
            raise ValueError("Region width must be positive.")
        if self.height <= 0:
            raise ValueError("Region height must be positive.")

    def metadata(self) -> dict[str, str | int]:
        """Return JSON-compatible region spec metadata."""
        return {
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }


@dataclass(frozen=True)
class RegionFrame:
    """RGB pixels extracted from one processed frame region."""

    frame_id: int
    region_name: str
    x: int
    y: int
    width: int
    height: int
    source_frame_width: int
    source_frame_height: int
    pixel_format: str
    data: bytes

    def metadata(self) -> dict[str, str | int]:
        """Return JSON-compatible region metadata without raw bytes."""
        return {
            "frame_id": self.frame_id,
            "region_name": self.region_name,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "source_frame_width": self.source_frame_width,
            "source_frame_height": self.source_frame_height,
            "pixel_format": self.pixel_format,
        }


def region_spec_from_config(name: str, config: RegionConfig) -> RegionSpec:
    """Build a validated region spec from a configured ROI preset."""
    return RegionSpec(
        name=name,
        x=config.x,
        y=config.y,
        width=config.width,
        height=config.height,
    )


def extract_region(frame: ProcessedFrame, region: RegionSpec) -> RegionFrame:
    """Extract an RGB region from a processed frame."""
    if frame.pixel_format != "RGB":
        raise RegionExtractionError(
            f"Cannot extract region from pixel format {frame.pixel_format!r}; expected 'RGB'."
        )

    expected_frame_size = frame.width * frame.height * 3
    if len(frame.data) != expected_frame_size:
        raise RegionExtractionError(
            "Cannot extract region because frame data size does not match RGB dimensions: "
            f"expected {expected_frame_size}, got {len(frame.data)}."
        )

    region_right = region.x + region.width
    region_bottom = region.y + region.height
    if region_right > frame.width or region_bottom > frame.height:
        raise RegionExtractionError(
            "Region is outside frame bounds: "
            f"region={region.name!r} x={region.x} y={region.y} "
            f"width={region.width} height={region.height}, "
            f"frame_width={frame.width}, frame_height={frame.height}."
        )

    row_size = frame.width * 3
    region_row_size = region.width * 3
    output = bytearray(region.width * region.height * 3)

    for row_offset in range(region.height):
        source_start = ((region.y + row_offset) * row_size) + (region.x * 3)
        source_end = source_start + region_row_size
        target_start = row_offset * region_row_size
        output[target_start : target_start + region_row_size] = frame.data[source_start:source_end]

    return RegionFrame(
        frame_id=frame.frame_id,
        region_name=region.name,
        x=region.x,
        y=region.y,
        width=region.width,
        height=region.height,
        source_frame_width=frame.width,
        source_frame_height=frame.height,
        pixel_format="RGB",
        data=bytes(output),
    )


def save_region_sample_ppm(region_frame: RegionFrame, path: Path | str) -> Path:
    """Save an RGB region frame as a binary PPM image."""
    if region_frame.pixel_format != "RGB":
        raise RegionExtractionError(
            f"Cannot save region with pixel format {region_frame.pixel_format!r}; expected 'RGB'."
        )

    expected_rgb_size = region_frame.width * region_frame.height * 3
    if len(region_frame.data) != expected_rgb_size:
        raise RegionExtractionError(
            "Cannot save region because data size does not match RGB dimensions: "
            f"expected {expected_rgb_size}, got {len(region_frame.data)}."
        )

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    header = f"P6\n{region_frame.width} {region_frame.height}\n255\n".encode("ascii")

    with output_path.open("wb") as file:
        file.write(header)
        file.write(region_frame.data)

    return output_path
