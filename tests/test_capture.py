from datetime import UTC

from genshin_ai.perception.capture import MockCaptureSource
from genshin_ai.perception.frame import CapturedFrame


def test_mock_capture_source_returns_captured_frame() -> None:
    source = MockCaptureSource(width=1280, height=720)

    frame = source.capture_frame()

    assert isinstance(frame, CapturedFrame)
    assert frame.source == "mock"
    assert frame.data is None


def test_mock_capture_source_increments_frame_id() -> None:
    source = MockCaptureSource(width=1280, height=720)

    first = source.capture_frame()
    second = source.capture_frame()

    assert first.frame_id == 1
    assert second.frame_id == 2


def test_mock_capture_source_preserves_dimensions() -> None:
    source = MockCaptureSource(width=960, height=540)

    frame = source.capture_frame()

    assert frame.width == 960
    assert frame.height == 540


def test_captured_frame_metadata_is_serializable_without_data() -> None:
    source = MockCaptureSource(width=1280, height=720, include_fake_data=True)

    frame = source.capture_frame()
    metadata = frame.metadata()

    assert metadata["frame_id"] == 1
    assert metadata["width"] == 1280
    assert metadata["height"] == 720
    assert metadata["source"] == "mock"
    assert "captured_at_utc" in metadata
    assert "data" not in metadata
    assert frame.captured_at_utc.tzinfo == UTC
    assert frame.data is not None
