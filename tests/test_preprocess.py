import importlib
from pathlib import Path

import pytest

from genshin_ai.perception.frame import CapturedFrame, ProcessedFrame
from genshin_ai.perception.preprocess import (
    FramePreprocessingError,
    FramePreprocessorDependencyError,
    preprocess_bgra_frame,
    preprocess_frame,
    processed_frame_sample_path,
    save_processed_frame_sample_ppm,
)


def test_preprocess_bgra_frame_converts_bgra_to_rgb() -> None:
    frame = CapturedFrame(
        frame_id=1,
        width=2,
        height=1,
        source="test",
        data=bytes((10, 20, 30, 255, 40, 50, 60, 255)),
    )

    processed = preprocess_bgra_frame(frame, target_width=2, target_height=1)

    assert processed.data == bytes((30, 20, 10, 60, 50, 40))
    assert processed.pixel_format == "RGB"


def test_preprocess_frame_python_backend_preserves_current_behavior() -> None:
    frame = CapturedFrame(
        frame_id=1,
        width=2,
        height=1,
        source="test",
        data=bytes((10, 20, 30, 255, 40, 50, 60, 255)),
    )

    processed = preprocess_frame(frame, target_width=2, target_height=1, backend="python")

    assert processed.width == 2
    assert processed.height == 1
    assert processed.source_frame_width == 2
    assert processed.source_frame_height == 1
    assert processed.data == bytes((30, 20, 10, 60, 50, 40))
    assert processed.pixel_format == "RGB"


def test_preprocess_frame_rejects_unknown_backend() -> None:
    frame = CapturedFrame(
        frame_id=1,
        width=1,
        height=1,
        source="test",
        data=bytes((0, 0, 0, 255)),
    )

    with pytest.raises(ValueError, match="Unknown preprocessing backend"):
        preprocess_frame(frame, target_width=1, target_height=1, backend="unknown")


def test_preprocess_frame_pillow_backend_reports_missing_dependency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = CapturedFrame(
        frame_id=1,
        width=1,
        height=1,
        source="test",
        data=bytes((0, 0, 10, 255)),
    )

    def import_module_without_pillow(name: str) -> object:
        if name == "PIL.Image":
            raise ModuleNotFoundError(name)
        return importlib.import_module(name)

    monkeypatch.setattr(importlib, "import_module", import_module_without_pillow)

    with pytest.raises(FramePreprocessorDependencyError, match="Pillow is required"):
        preprocess_frame(frame, target_width=1, target_height=1, backend="pillow")


def test_preprocess_frame_pillow_backend_returns_rgb_frame_when_available() -> None:
    pytest.importorskip("PIL.Image")
    frame = CapturedFrame(
        frame_id=1,
        width=2,
        height=1,
        source="test",
        data=bytes((10, 20, 30, 255, 40, 50, 60, 255)),
    )

    processed = preprocess_frame(frame, target_width=1, target_height=1, backend="pillow")

    assert processed.width == 1
    assert processed.height == 1
    assert processed.source_frame_width == 2
    assert processed.source_frame_height == 1
    assert processed.pixel_format == "RGB"
    assert len(processed.data) == 3


def test_preprocess_bgra_frame_resizes_to_target_dimensions() -> None:
    frame = CapturedFrame(
        frame_id=1,
        width=2,
        height=2,
        source="test",
        data=bytes(
            (
                0,
                0,
                10,
                255,
                0,
                0,
                20,
                255,
                0,
                0,
                30,
                255,
                0,
                0,
                40,
                255,
            )
        ),
    )

    processed = preprocess_bgra_frame(frame, target_width=1, target_height=1)

    assert processed.width == 1
    assert processed.height == 1
    assert processed.source_frame_width == 2
    assert processed.source_frame_height == 2
    assert processed.data == bytes((10, 0, 0))


def test_preprocess_bgra_frame_rejects_missing_data() -> None:
    frame = CapturedFrame(frame_id=1, width=1, height=1, source="test", data=None)

    with pytest.raises(FramePreprocessingError, match="frame.data is None"):
        preprocess_bgra_frame(frame, target_width=1, target_height=1)


def test_preprocess_bgra_frame_rejects_invalid_target_size() -> None:
    frame = CapturedFrame(
        frame_id=1,
        width=1,
        height=1,
        source="test",
        data=bytes((0, 0, 0, 255)),
    )

    with pytest.raises(FramePreprocessingError, match="target_width"):
        preprocess_bgra_frame(frame, target_width=0, target_height=1)

    with pytest.raises(FramePreprocessingError, match="target_height"):
        preprocess_bgra_frame(frame, target_width=1, target_height=0)


def test_preprocess_bgra_frame_rejects_invalid_bgra_size() -> None:
    frame = CapturedFrame(
        frame_id=1,
        width=2,
        height=1,
        source="test",
        data=bytes((0, 0, 0, 255)),
    )

    with pytest.raises(FramePreprocessingError, match="data size does not match"):
        preprocess_bgra_frame(frame, target_width=1, target_height=1)


def test_processed_frame_metadata_is_serializable_without_data() -> None:
    frame = ProcessedFrame(
        frame_id=7,
        width=1280,
        height=720,
        source_frame_width=2560,
        source_frame_height=1440,
        source="mss.preprocess",
        data=bytes((1, 2, 3)),
    )

    metadata = frame.metadata()

    assert metadata["frame_id"] == 7
    assert metadata["width"] == 1280
    assert metadata["height"] == 720
    assert metadata["source_frame_width"] == 2560
    assert metadata["source_frame_height"] == 1440
    assert metadata["pixel_format"] == "RGB"
    assert "processed_at_utc" in metadata
    assert "data" not in metadata


def test_save_processed_frame_sample_ppm_writes_valid_ppm(tmp_path: Path) -> None:
    frame = ProcessedFrame(
        frame_id=1,
        width=2,
        height=1,
        source_frame_width=2,
        source_frame_height=1,
        source="test.preprocess",
        data=bytes((30, 20, 10, 60, 50, 40)),
    )

    output_path = save_processed_frame_sample_ppm(frame, tmp_path / "processed.ppm")

    assert output_path.exists()
    assert output_path.read_bytes() == b"P6\n2 1\n255\n" + bytes((30, 20, 10, 60, 50, 40))


def test_processed_frame_sample_path_includes_frame_id(tmp_path: Path) -> None:
    frame = ProcessedFrame(
        frame_id=42,
        width=1,
        height=1,
        source_frame_width=1,
        source_frame_height=1,
        source="test.preprocess",
        data=bytes((0, 0, 0)),
    )

    path = processed_frame_sample_path(tmp_path, frame)

    assert path.name == "processed_frame_000042.ppm"
