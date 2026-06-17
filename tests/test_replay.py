import json
from pathlib import Path

import pytest

from genshin_ai.cli import main
from genshin_ai.perception.frame import ProcessedFrame
from genshin_ai.perception.replay import (
    ProcessedFrameReplaySource,
    ReplayEndOfSequenceError,
    ReplayFrameError,
    ReplayLoadedFrame,
)


def test_replay_source_loads_valid_ppm_frame(tmp_path: Path) -> None:
    payload = bytes((30, 20, 10, 60, 50, 40))
    _write_ppm(tmp_path / "processed_frame_000001.ppm", width=2, height=1, payload=payload)

    source = ProcessedFrameReplaySource(tmp_path)
    frame = source.load_next_frame()

    assert frame.frame_id == 1
    assert frame.width == 2
    assert frame.height == 1
    assert frame.source_frame_width == 2
    assert frame.source_frame_height == 1
    assert frame.source == "replay.ppm"
    assert frame.pixel_format == "RGB"
    assert frame.data == payload


def test_replay_source_load_next_returns_loaded_frame_with_path(tmp_path: Path) -> None:
    frame_path = tmp_path / "processed_frame_000001.ppm"
    payload = b"\x01\x02\x03"
    _write_ppm(frame_path, width=1, height=1, payload=payload)

    source = ProcessedFrameReplaySource(tmp_path)
    loaded = source.load_next()

    assert isinstance(loaded, ReplayLoadedFrame)
    assert loaded.path == frame_path
    assert loaded.frame.frame_id == 1
    assert loaded.frame.data == payload


def test_replay_source_load_next_frame_returns_processed_frame_only(tmp_path: Path) -> None:
    _write_ppm(
        tmp_path / "processed_frame_000001.ppm",
        width=1,
        height=1,
        payload=b"\x01\x02\x03",
    )

    source = ProcessedFrameReplaySource(tmp_path)
    frame = source.load_next_frame()

    assert isinstance(frame, ProcessedFrame)


def test_replay_source_loads_multiple_frames_ordered_by_name(tmp_path: Path) -> None:
    _write_ppm(tmp_path / "processed_frame_000002.ppm", width=1, height=1, payload=b"\x02\x00\x00")
    _write_ppm(tmp_path / "processed_frame_000001.ppm", width=1, height=1, payload=b"\x01\x00\x00")

    source = ProcessedFrameReplaySource(tmp_path)
    first_frame = source.load_next_frame()
    second_frame = source.load_next_frame()

    assert first_frame.frame_id == 1
    assert first_frame.data == b"\x01\x00\x00"
    assert second_frame.frame_id == 2
    assert second_frame.data == b"\x02\x00\x00"


def test_replay_source_rejects_missing_directory(tmp_path: Path) -> None:
    with pytest.raises(ReplayFrameError, match="directory does not exist"):
        ProcessedFrameReplaySource(tmp_path / "missing")


def test_replay_source_rejects_directory_without_ppm(tmp_path: Path) -> None:
    (tmp_path / "not-a-frame.txt").write_text("test", encoding="utf-8")

    with pytest.raises(ReplayFrameError, match="No .ppm replay frames"):
        ProcessedFrameReplaySource(tmp_path)


def test_replay_source_rejects_invalid_magic(tmp_path: Path) -> None:
    (tmp_path / "frame.ppm").write_bytes(b"P3\n1 1\n255\n\x00\x00\x00")

    source = ProcessedFrameReplaySource(tmp_path)
    with pytest.raises(ReplayFrameError, match="expected P6"):
        source.load_next_frame()


def test_replay_source_invalid_frame_does_not_advance_sequence(tmp_path: Path) -> None:
    (tmp_path / "frame.ppm").write_bytes(b"P3\n1 1\n255\n\x00\x00\x00")

    source = ProcessedFrameReplaySource(tmp_path)

    with pytest.raises(ReplayFrameError, match="expected P6"):
        source.load_next_frame()
    with pytest.raises(ReplayFrameError, match="expected P6"):
        source.load_next_frame()


def test_replay_source_retries_first_invalid_frame_before_second_valid_frame(
    tmp_path: Path,
) -> None:
    (tmp_path / "processed_frame_000001.ppm").write_bytes(b"P3\n1 1\n255\n\x00\x00\x00")
    _write_ppm(
        tmp_path / "processed_frame_000002.ppm",
        width=1,
        height=1,
        payload=b"\x01\x02\x03",
    )

    source = ProcessedFrameReplaySource(tmp_path)

    with pytest.raises(ReplayFrameError, match="expected P6"):
        source.load_next()
    with pytest.raises(ReplayFrameError, match="expected P6"):
        source.load_next()


def test_replay_source_rejects_short_payload(tmp_path: Path) -> None:
    (tmp_path / "frame.ppm").write_bytes(b"P6\n2 1\n255\n\x00\x00\x00")

    source = ProcessedFrameReplaySource(tmp_path)
    with pytest.raises(ReplayFrameError, match="payload size"):
        source.load_next_frame()


def test_replay_source_rejects_long_payload(tmp_path: Path) -> None:
    (tmp_path / "frame.ppm").write_bytes(b"P6\n1 1\n255\n\x00\x00\x00\x00")

    source = ProcessedFrameReplaySource(tmp_path)
    with pytest.raises(ReplayFrameError, match="payload size"):
        source.load_next_frame()


def test_replay_source_rejects_unsupported_max_value(tmp_path: Path) -> None:
    (tmp_path / "frame.ppm").write_bytes(b"P6\n1 1\n254\n\x00\x00\x00")

    source = ProcessedFrameReplaySource(tmp_path)
    with pytest.raises(ReplayFrameError, match="max value"):
        source.load_next_frame()


def test_replay_source_raises_at_end_of_sequence(tmp_path: Path) -> None:
    _write_ppm(tmp_path / "frame.ppm", width=1, height=1, payload=b"\x00\x00\x00")
    source = ProcessedFrameReplaySource(tmp_path)

    source.load_next_frame()

    with pytest.raises(ReplayEndOfSequenceError, match="No more replay frames"):
        source.load_next_frame()


def test_replay_source_wraps_read_errors_as_replay_frame_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame_path = tmp_path / "frame.ppm"
    _write_ppm(frame_path, width=1, height=1, payload=b"\x00\x00\x00")
    source = ProcessedFrameReplaySource(tmp_path)

    def raise_os_error(self: Path) -> bytes:
        raise OSError("permission denied")

    monkeypatch.setattr(Path, "read_bytes", raise_os_error)

    with pytest.raises(ReplayFrameError) as error_info:
        source.load_next()
    assert f"Failed to read replay frame file {frame_path}" in str(error_info.value)


def test_replay_smoke_cli_loads_frames_and_writes_events(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir()
    _write_ppm(
        frames_dir / "processed_frame_000001.ppm",
        width=1,
        height=1,
        payload=b"\x01\x02\x03",
    )
    _write_ppm(
        frames_dir / "processed_frame_000002.ppm",
        width=1,
        height=1,
        payload=b"\x04\x05\x06",
    )
    monkeypatch.chdir(tmp_path)

    main(["replay-smoke", "--frames-dir", str(frames_dir), "--limit", "2"])

    output = capsys.readouterr().out
    assert "Frames loaded: 2" in output

    event_files = list((tmp_path / "runs").glob("*/logs/events.jsonl"))
    assert len(event_files) == 1
    events = [
        json.loads(line)
        for line in event_files[0].read_text(encoding="utf-8").splitlines()
    ]
    event_names = [event["event"] for event in events]

    assert event_names == [
        "replay_smoke_started",
        "replay_frame_loaded",
        "replay_frame_loaded",
        "replay_smoke_finished",
    ]
    assert events[1]["data"]["frame_id"] == 1
    assert events[1]["data"]["source"] == "replay.ppm"
    assert events[1]["data"]["frame_path"] == str(frames_dir / "processed_frame_000001.ppm")
    assert events[2]["data"]["frame_path"] == str(frames_dir / "processed_frame_000002.ppm")
    assert events[-1]["data"]["frames_loaded"] == 2


def test_replay_smoke_cli_finishes_on_end_of_sequence_after_loading_frame(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir()
    _write_ppm(
        frames_dir / "processed_frame_000001.ppm",
        width=1,
        height=1,
        payload=b"\x01\x02\x03",
    )
    monkeypatch.chdir(tmp_path)

    main(["replay-smoke", "--frames-dir", str(frames_dir), "--limit", "5"])

    output = capsys.readouterr().out
    assert "Frames loaded: 1" in output

    event_files = list((tmp_path / "runs").glob("*/logs/events.jsonl"))
    assert len(event_files) == 1
    events = [
        json.loads(line)
        for line in event_files[0].read_text(encoding="utf-8").splitlines()
    ]
    event_names = [event["event"] for event in events]

    assert event_names == [
        "replay_smoke_started",
        "replay_frame_loaded",
        "replay_smoke_finished",
    ]
    assert events[1]["data"]["frame_path"] == str(frames_dir / "processed_frame_000001.ppm")
    assert events[-1]["data"]["frames_loaded"] == 1


def _write_ppm(path: Path, width: int, height: int, payload: bytes) -> None:
    path.write_bytes(f"P6\n{width} {height}\n255\n".encode("ascii") + payload)
