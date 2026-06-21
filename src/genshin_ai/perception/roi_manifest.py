"""Batch ROI extraction manifest for processed replay frames."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from genshin_ai.core.logging import JsonlEventLogger, JsonValue, LogEvent
from genshin_ai.perception.regions import RegionSpec, extract_region, save_region_sample_ppm
from genshin_ai.perception.replay import ProcessedFrameReplaySource, ReplayEndOfSequenceError


@dataclass(frozen=True)
class RoiManifestEntry:
    """One extracted ROI sample record tied to its source replay frame."""

    frame_id: int
    frame_path: str
    region_name: str
    region_source: str
    x: int
    y: int
    width: int
    height: int
    source_frame_width: int
    source_frame_height: int
    pixel_format: str
    sample_path: str | None

    def to_dict(self) -> dict[str, str | int | None]:
        """Serialize the manifest entry into JSON-compatible values."""
        return {
            "frame_id": self.frame_id,
            "frame_path": self.frame_path,
            "region_name": self.region_name,
            "region_source": self.region_source,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "source_frame_width": self.source_frame_width,
            "source_frame_height": self.source_frame_height,
            "pixel_format": self.pixel_format,
            "sample_path": self.sample_path,
        }


@dataclass(frozen=True)
class RoiManifest:
    """Manifest for a batch of ROI extractions from replay frames."""

    run_id: str
    frames_dir: str
    regions: tuple[RegionSpec, ...]
    entries: tuple[RoiManifestEntry, ...]

    def to_dict(self) -> dict[str, object]:
        """Serialize the manifest into JSON-compatible values."""
        return {
            "run_id": self.run_id,
            "frames_dir": self.frames_dir,
            "regions": [region.metadata() for region in self.regions],
            "entries": [entry.to_dict() for entry in self.entries],
        }


def save_roi_manifest(manifest: RoiManifest, path: Path | str) -> Path:
    """Save an ROI manifest as deterministic JSON."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return output_path


def extract_roi_batch(
    *,
    frames_dir: Path | str,
    regions: Sequence[RegionSpec],
    run_id: str,
    artifacts_dir: Path | str,
    limit: int,
    save_samples: bool = False,
    region_source: str = "config",
    event_logger: JsonlEventLogger | None = None,
) -> RoiManifest:
    """Extract all requested ROI regions from processed replay frames."""
    if limit <= 0:
        raise ValueError("ROI batch frame limit must be positive.")
    if not regions:
        raise ValueError("ROI batch requires at least one region.")
    if not region_source:
        raise ValueError("ROI batch region source must not be empty.")

    frames_dir_path = Path(frames_dir)
    artifacts_dir_path = Path(artifacts_dir)
    regions_tuple = tuple(regions)

    _emit(
        event_logger,
        "roi_batch_started",
        {
            "frames_dir": str(frames_dir_path),
            "limit": limit,
            "save_samples": save_samples,
            "region_source": region_source,
            "regions": [region.metadata() for region in regions_tuple],
        },
    )

    source = ProcessedFrameReplaySource(frames_dir_path)
    entries: list[RoiManifestEntry] = []
    frames_loaded = 0
    samples_dir = artifacts_dir_path / "roi"

    while frames_loaded < limit:
        try:
            loaded = source.load_next()
        except ReplayEndOfSequenceError:
            if frames_loaded > 0:
                break
            raise

        frames_loaded += 1
        for region in regions_tuple:
            region_frame = extract_region(loaded.frame, region)
            sample_path: str | None = None
            if save_samples:
                output_path = save_region_sample_ppm(
                    region_frame,
                    samples_dir / f"{region_frame.region_name}_{region_frame.frame_id:06d}.ppm",
                )
                sample_path = str(output_path)

            entry = RoiManifestEntry(
                frame_id=region_frame.frame_id,
                frame_path=str(loaded.path),
                region_name=region_frame.region_name,
                region_source=region_source,
                x=region_frame.x,
                y=region_frame.y,
                width=region_frame.width,
                height=region_frame.height,
                source_frame_width=region_frame.source_frame_width,
                source_frame_height=region_frame.source_frame_height,
                pixel_format=region_frame.pixel_format,
                sample_path=sample_path,
            )
            entries.append(entry)
            _emit(event_logger, "roi_batch_region_extracted", entry.to_dict())

    return RoiManifest(
        run_id=run_id,
        frames_dir=str(frames_dir_path),
        regions=regions_tuple,
        entries=tuple(entries),
    )


def _emit(
    event_logger: JsonlEventLogger | None,
    event: str,
    data: Mapping[str, JsonValue],
) -> None:
    if event_logger is None:
        return

    event_logger.emit(
        LogEvent(
            event=event,
            module="perception.roi_manifest",
            data=dict(data),
        )
    )
