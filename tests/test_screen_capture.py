import sys
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType

import pytest

from genshin_ai.perception.frame import CapturedFrame
from genshin_ai.perception.screen_capture import (
    MssScreenCaptureSource,
    ScreenCaptureDependencyError,
    sample_frame_path,
    save_frame_sample_ppm,
)


class FakeScreenshot:
    width = 2
    height = 1
    raw = bytes((10, 20, 30, 255, 40, 50, 60, 255))


class FakeMssInstance:
    def __init__(self, monitors: list[dict[str, int]]) -> None:
        self.monitors = monitors
        self.grabbed_monitors: list[dict[str, int]] = []
        self.close_calls = 0

    def grab(self, monitor: dict[str, int]) -> FakeScreenshot:
        self.grabbed_monitors.append(monitor)
        return FakeScreenshot()

    def close(self) -> None:
        self.close_calls += 1


class FakeMssModule(ModuleType):
    def __init__(self, monitors: list[dict[str, int]] | None = None) -> None:
        super().__init__("mss")
        self.monitors = monitors or [
            {"left": 0, "top": 0, "width": 3840, "height": 1080},
            {"left": 0, "top": 0, "width": 1920, "height": 1080},
        ]
        self.instances: list[FakeMssInstance] = []
        self.mss_calls = 0

    def mss(self) -> FakeMssInstance:
        self.mss_calls += 1
        instance = FakeMssInstance(self.monitors)
        self.instances.append(instance)
        return instance


def test_missing_mss_dependency_raises_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "mss", None)

    with pytest.raises(ScreenCaptureDependencyError, match="pip install"):
        MssScreenCaptureSource()


def test_mss_context_is_created_once_and_grab_runs_per_frame(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_mss = FakeMssModule()
    monkeypatch.setitem(sys.modules, "mss", fake_mss)

    source = MssScreenCaptureSource()
    try:
        first_frame = source.capture_frame()
        second_frame = source.capture_frame()
    finally:
        source.close()

    instance = fake_mss.instances[0]
    assert fake_mss.mss_calls == 1
    assert len(instance.grabbed_monitors) == 2
    assert instance.grabbed_monitors == [fake_mss.monitors[1], fake_mss.monitors[1]]
    assert first_frame.frame_id == 1
    assert second_frame.frame_id == 2
    assert first_frame.width == 2
    assert first_frame.height == 1
    assert first_frame.data == FakeScreenshot.raw


def test_mss_context_manager_closes_capture(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_mss = FakeMssModule()
    monkeypatch.setitem(sys.modules, "mss", fake_mss)

    with MssScreenCaptureSource() as source:
        frame = source.capture_frame()

    assert frame.frame_id == 1
    assert fake_mss.instances[0].close_calls == 1


def test_mss_close_is_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_mss = FakeMssModule()
    monkeypatch.setitem(sys.modules, "mss", fake_mss)

    source = MssScreenCaptureSource()
    source.close()
    source.close()

    assert fake_mss.instances[0].close_calls == 1


def test_mss_capture_after_close_raises_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_mss = FakeMssModule()
    monkeypatch.setitem(sys.modules, "mss", fake_mss)
    source = MssScreenCaptureSource()
    source.close()

    with pytest.raises(RuntimeError, match="closed"):
        source.capture_frame()


def test_mss_invalid_monitor_index_raises_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_mss = FakeMssModule()
    monkeypatch.setitem(sys.modules, "mss", fake_mss)

    with pytest.raises(ValueError, match="Monitor index 2 is not available"):
        MssScreenCaptureSource(monitor_index=2)

    assert fake_mss.instances[0].close_calls == 1


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
