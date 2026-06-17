"""Frame preprocessing and resize utilities."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, cast

from genshin_ai.perception.frame import CapturedFrame, ProcessedFrame


class FramePreprocessingError(RuntimeError):
    """Raised when a captured frame cannot be preprocessed."""


class FramePreprocessorDependencyError(RuntimeError):
    """Raised when an optional preprocessing backend dependency is missing."""


def preprocess_frame(
    frame: CapturedFrame,
    target_width: int,
    target_height: int,
    backend: str = "python",
) -> ProcessedFrame:
    """Preprocess a captured BGRA frame using the selected backend."""
    if backend == "python":
        return preprocess_bgra_frame(
            frame,
            target_width=target_width,
            target_height=target_height,
        )
    if backend == "pillow":
        return _preprocess_bgra_frame_with_pillow(
            frame,
            target_width=target_width,
            target_height=target_height,
        )
    raise ValueError(f"Unknown preprocessing backend: {backend}")


def preprocess_bgra_frame(
    frame: CapturedFrame,
    target_width: int,
    target_height: int,
) -> ProcessedFrame:
    """Convert a BGRA captured frame to resized RGB using nearest-neighbor."""
    _validate_target_size(target_width, target_height)
    _validate_bgra_frame(frame)

    if frame.data is None:
        raise FramePreprocessingError("Cannot preprocess frame because frame.data is None.")

    rgb_data = _resize_bgra_to_rgb_nearest_neighbor(
        bgra_data=frame.data,
        source_width=frame.width,
        source_height=frame.height,
        target_width=target_width,
        target_height=target_height,
    )

    return ProcessedFrame(
        frame_id=frame.frame_id,
        width=target_width,
        height=target_height,
        source_frame_width=frame.width,
        source_frame_height=frame.height,
        source=f"{frame.source}.preprocess",
        data=rgb_data,
    )


def _preprocess_bgra_frame_with_pillow(
    frame: CapturedFrame,
    target_width: int,
    target_height: int,
) -> ProcessedFrame:
    _validate_target_size(target_width, target_height)
    _validate_bgra_frame(frame)

    if frame.data is None:
        raise FramePreprocessingError("Cannot preprocess frame because frame.data is None.")

    try:
        image_module = importlib.import_module("PIL.Image")
    except ModuleNotFoundError as error:
        raise FramePreprocessorDependencyError(
            "Pillow is required for preprocess backend 'pillow'. "
            "Install it with: pip install -e \".[image]\""
        ) from error

    image_api = cast(Any, image_module)
    resampling = getattr(image_api, "Resampling", image_api)
    image = image_api.frombytes(
        "RGBA",
        (frame.width, frame.height),
        frame.data,
        "raw",
        "BGRA",
    )
    resized = image.convert("RGB").resize(
        (target_width, target_height),
        resample=resampling.NEAREST,
    )

    return ProcessedFrame(
        frame_id=frame.frame_id,
        width=target_width,
        height=target_height,
        source_frame_width=frame.width,
        source_frame_height=frame.height,
        source=f"{frame.source}.preprocess",
        data=resized.tobytes(),
        pixel_format="RGB",
    )


def save_processed_frame_sample_ppm(frame: ProcessedFrame, output_path: Path | str) -> Path:
    """Save an RGB processed frame as a binary PPM image."""
    expected_rgb_size = frame.width * frame.height * 3
    if len(frame.data) != expected_rgb_size:
        raise FramePreprocessingError(
            "Cannot save processed frame because data size does not match RGB dimensions: "
            f"expected {expected_rgb_size}, got {len(frame.data)}."
        )

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    header = f"P6\n{frame.width} {frame.height}\n255\n".encode("ascii")

    with path.open("wb") as file:
        file.write(header)
        file.write(frame.data)

    return path


def processed_frame_sample_path(captures_dir: Path | str, frame: ProcessedFrame) -> Path:
    """Build a deterministic processed sample filename containing the frame id."""
    return Path(captures_dir) / f"processed_frame_{frame.frame_id:06d}.ppm"


def _validate_target_size(target_width: int, target_height: int) -> None:
    if target_width <= 0:
        raise FramePreprocessingError("target_width must be positive.")
    if target_height <= 0:
        raise FramePreprocessingError("target_height must be positive.")


def _validate_bgra_frame(frame: CapturedFrame) -> None:
    if frame.data is None:
        raise FramePreprocessingError("Cannot preprocess frame because frame.data is None.")

    expected_bgra_size = frame.width * frame.height * 4
    if len(frame.data) != expected_bgra_size:
        raise FramePreprocessingError(
            "Cannot preprocess frame because frame.data size does not match "
            f"BGRA dimensions: expected {expected_bgra_size}, got {len(frame.data)}."
        )


def _resize_bgra_to_rgb_nearest_neighbor(
    bgra_data: bytes,
    source_width: int,
    source_height: int,
    target_width: int,
    target_height: int,
) -> bytes:
    output = bytearray(target_width * target_height * 3)

    for target_y in range(target_height):
        source_y = (target_y * source_height) // target_height

        for target_x in range(target_width):
            source_x = (target_x * source_width) // target_width
            source_index = ((source_y * source_width) + source_x) * 4
            target_index = ((target_y * target_width) + target_x) * 3

            blue = bgra_data[source_index]
            green = bgra_data[source_index + 1]
            red = bgra_data[source_index + 2]

            output[target_index] = red
            output[target_index + 1] = green
            output[target_index + 2] = blue

    return bytes(output)
