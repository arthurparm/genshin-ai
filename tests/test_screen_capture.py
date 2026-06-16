import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from genshin_ai.perception.frame import CapturedFrame
from genshin_ai.perception.screen_capture import (
    MssScreenCaptureSource,
    ScreenCaptureDependencyError,
    sample_frame_path,
    save_frame_sample_ppm,
)


def test_missing_mss_dependency_raises_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "mss", None)

    with pytest.raises(ScreenCaptureDependencyError, match="pip install"):
        MssScreenCaptureSource()


def test_save_frame_sample_ppm_writes_file(tmp_path: Path) -> None:
    frame = CapturedFrame(
        frame_id=1,
        width=2,
        height=1,
        captured_at_utc=datetime.now(UTC),
        source="mss",
        data=bytes(
            (
                10,
                20,
                30,
                255,
                40,
                50,
                60,
                255,
            )
        ),
    )

    output_path = save_frame_sample_ppm(frame, tmp_path / "sample.ppm")

    assert output_path.exists()
    assert output_path.read_bytes() == b"P6\n2 1\n255\n" + bytes((30, 20, 10, 60, 50, 40))


def test_sample_frame_path_includes_frame_id(tmp_path: Path) -> None:
    frame = CapturedFrame(
        frame_id=42,
        width=1,
        height=1,
        source="mss",
        data=bytes((0, 0, 0, 255)),
    )

    path = sample_frame_path(tmp_path, frame)

    assert path.name == "frame_000042.ppm"


def test_save_frame_sample_ppm_rejects_missing_data(tmp_path: Path) -> None:
    frame = CapturedFrame(frame_id=1, width=1, height=1, source="mss", data=None)

    with pytest.raises(ValueError, match="frame.data is None"):
        save_frame_sample_ppm(frame, tmp_path / "sample.ppm")


def test_save_frame_sample_ppm_rejects_invalid_bgra_size(tmp_path: Path) -> None:
    frame = CapturedFrame(frame_id=1, width=2, height=1, source="mss", data=bytes((0, 0, 0, 0)))

    with pytest.raises(ValueError, match="data size does not match"):
        save_frame_sample_ppm(frame, tmp_path / "sample.ppm")
