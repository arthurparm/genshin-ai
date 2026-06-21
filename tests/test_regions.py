import json
from pathlib import Path
from typing import Any

import pytest

from genshin_ai.cli import main
from genshin_ai.core.config import RegionConfig
from genshin_ai.perception.frame import ProcessedFrame
from genshin_ai.perception.regions import (
    RegionExtractionError,
    RegionFrame,
    RegionSpec,
    extract_region,
    region_spec_from_config,
    save_region_sample_ppm,
)


def test_region_spec_accepts_valid_values() -> None:
    region = RegionSpec(name="hud_health", x=1, y=2, width=3, height=4)

    assert region.name == "hud_health"
    assert region.x == 1
    assert region.y == 2
    assert region.width == 3
    assert region.height == 4


@pytest.mark.parametrize("name", ["minimap", "quest_text", "interaction-prompt"])
def test_region_spec_accepts_safe_names(name: str) -> None:
    region = RegionSpec(name=name, x=0, y=0, width=1, height=1)

    assert region.name == name


def test_region_spec_rejects_empty_name() -> None:
    with pytest.raises(ValueError, match="name must not be empty"):
        RegionSpec(name="", x=0, y=0, width=1, height=1)


@pytest.mark.parametrize("name", ["mini/map", "mini\\map", "mini.map", "mini map", ".."])
def test_region_spec_rejects_unsafe_names(name: str) -> None:
    with pytest.raises(ValueError, match="letters, numbers, underscores, or hyphens"):
        RegionSpec(name=name, x=0, y=0, width=1, height=1)


@pytest.mark.parametrize(("x", "y"), [(-1, 0), (0, -1)])
def test_region_spec_rejects_negative_coordinates(x: int, y: int) -> None:
    with pytest.raises(ValueError, match="must be non-negative"):
        RegionSpec(name="test", x=x, y=y, width=1, height=1)


@pytest.mark.parametrize(("width", "height"), [(0, 1), (-1, 1), (1, 0), (1, -1)])
def test_region_spec_rejects_non_positive_size(width: int, height: int) -> None:
    with pytest.raises(ValueError, match="must be positive"):
        RegionSpec(name="test", x=0, y=0, width=width, height=height)


def test_region_spec_metadata() -> None:
    region = RegionSpec(name="minimap", x=1, y=2, width=3, height=4)

    assert region.metadata() == {
        "name": "minimap",
        "x": 1,
        "y": 2,
        "width": 3,
        "height": 4,
    }


def test_region_spec_from_config() -> None:
    region = region_spec_from_config(
        "interaction-prompt",
        RegionConfig(x=10, y=20, width=30, height=40),
    )

    assert region == RegionSpec(
        name="interaction-prompt",
        x=10,
        y=20,
        width=30,
        height=40,
    )


def test_extract_region_returns_expected_rgb_bytes() -> None:
    frame = _processed_frame(
        width=3,
        height=2,
        data=bytes(
            (
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                10,
                11,
                12,
                13,
                14,
                15,
                16,
                17,
                18,
            )
        ),
    )
    region = RegionSpec(name="center_right", x=1, y=0, width=2, height=2)

    region_frame = extract_region(frame, region)

    assert region_frame == RegionFrame(
        frame_id=42,
        region_name="center_right",
        x=1,
        y=0,
        width=2,
        height=2,
        source_frame_width=3,
        source_frame_height=2,
        pixel_format="RGB",
        data=bytes((4, 5, 6, 7, 8, 9, 13, 14, 15, 16, 17, 18)),
    )


def test_extract_region_rejects_region_outside_frame() -> None:
    frame = _processed_frame(width=2, height=2, data=bytes(range(12)))
    region = RegionSpec(name="outside", x=1, y=1, width=2, height=1)

    with pytest.raises(RegionExtractionError, match="outside frame bounds"):
        extract_region(frame, region)


def test_extract_region_rejects_non_rgb_frame() -> None:
    frame = _processed_frame(width=1, height=1, data=b"\x00\x00\x00", pixel_format="BGR")
    region = RegionSpec(name="test", x=0, y=0, width=1, height=1)

    with pytest.raises(RegionExtractionError, match="expected 'RGB'"):
        extract_region(frame, region)


def test_extract_region_rejects_invalid_frame_payload_size() -> None:
    frame = _processed_frame(width=2, height=1, data=b"\x00\x00\x00")
    region = RegionSpec(name="test", x=0, y=0, width=1, height=1)

    with pytest.raises(RegionExtractionError, match="data size does not match"):
        extract_region(frame, region)


def test_region_frame_metadata_excludes_bytes() -> None:
    region_frame = RegionFrame(
        frame_id=1,
        region_name="test",
        x=0,
        y=0,
        width=1,
        height=1,
        source_frame_width=2,
        source_frame_height=2,
        pixel_format="RGB",
        data=b"\x01\x02\x03",
    )

    metadata = region_frame.metadata()

    assert metadata == {
        "frame_id": 1,
        "region_name": "test",
        "x": 0,
        "y": 0,
        "width": 1,
        "height": 1,
        "source_frame_width": 2,
        "source_frame_height": 2,
        "pixel_format": "RGB",
    }
    assert "data" not in metadata


def test_save_region_sample_ppm_writes_valid_ppm(tmp_path: Path) -> None:
    region_frame = RegionFrame(
        frame_id=1,
        region_name="test",
        x=0,
        y=0,
        width=2,
        height=1,
        source_frame_width=2,
        source_frame_height=1,
        pixel_format="RGB",
        data=b"\x01\x02\x03\x04\x05\x06",
    )

    output_path = save_region_sample_ppm(region_frame, tmp_path / "nested" / "region.ppm")

    assert output_path == tmp_path / "nested" / "region.ppm"
    assert output_path.read_bytes() == b"P6\n2 1\n255\n\x01\x02\x03\x04\x05\x06"


def test_save_region_sample_ppm_rejects_invalid_payload_size(tmp_path: Path) -> None:
    region_frame = RegionFrame(
        frame_id=1,
        region_name="test",
        x=0,
        y=0,
        width=2,
        height=1,
        source_frame_width=2,
        source_frame_height=1,
        pixel_format="RGB",
        data=b"\x01\x02\x03",
    )

    with pytest.raises(RegionExtractionError, match="data size does not match"):
        save_region_sample_ppm(region_frame, tmp_path / "region.ppm")


def test_roi_smoke_cli_extracts_replay_region_and_logs_frame_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir()
    _write_ppm(
        frames_dir / "processed_frame_000001.ppm",
        width=2,
        height=1,
        payload=b"\x01\x02\x03\x04\x05\x06",
    )
    monkeypatch.chdir(tmp_path)

    main(
        [
            "roi-smoke",
            "--frames-dir",
            str(frames_dir),
            "--x",
            "1",
            "--y",
            "0",
            "--width",
            "1",
            "--height",
            "1",
            "--name",
            "test",
            "--limit",
            "1",
            "--save-samples",
        ]
    )

    output = capsys.readouterr().out
    assert "Frames loaded: 1" in output
    assert "Samples saved: 1" in output

    event_files = list((tmp_path / "runs").glob("*/logs/events.jsonl"))
    assert len(event_files) == 1
    events = [
        json.loads(line)
        for line in event_files[0].read_text(encoding="utf-8").splitlines()
    ]

    assert [event["event"] for event in events] == [
        "roi_smoke_started",
        "roi_extracted",
        "roi_sample_saved",
        "roi_smoke_finished",
    ]
    assert events[1]["data"]["region_name"] == "test"
    assert events[1]["data"]["region_source"] == "manual"
    assert events[1]["data"]["region"] == {
        "name": "test",
        "x": 1,
        "y": 0,
        "width": 1,
        "height": 1,
    }
    assert events[1]["data"]["source_frame_id"] == 1
    assert events[1]["data"]["frame_path"] == str(frames_dir / "processed_frame_000001.ppm")

    sample_files = list((tmp_path / "runs").glob("*/artifacts/roi/test_000001.ppm"))
    assert len(sample_files) == 1
    assert sample_files[0].read_bytes() == b"P6\n1 1\n255\n\x04\x05\x06"


def test_roi_smoke_cli_fails_clearly_for_region_outside_frame(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
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

    with pytest.raises(SystemExit, match="outside frame bounds"):
        main(
            [
                "roi-smoke",
                "--frames-dir",
                str(frames_dir),
                "--x",
                "0",
                "--y",
                "0",
                "--width",
                "2",
                "--height",
                "1",
                "--name",
                "test",
                "--limit",
                "1",
            ]
        )


def test_roi_smoke_cli_requires_complete_manual_region(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
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

    with pytest.raises(SystemExit, match="Manual ROI mode requires"):
        main(
            [
                "roi-smoke",
                "--frames-dir",
                str(frames_dir),
                "--x",
                "0",
                "--y",
                "0",
                "--width",
                "1",
                "--limit",
                "1",
            ]
        )


def test_roi_smoke_cli_extracts_configured_region(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir()
    _write_ppm(
        frames_dir / "processed_frame_000001.ppm",
        width=2,
        height=1,
        payload=b"\x01\x02\x03\x04\x05\x06",
    )
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        """
[regions.minimap]
x = 1
y = 0
width = 1
height = 1
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    main(
        [
            "--config",
            str(config_file),
            "roi-smoke",
            "--frames-dir",
            str(frames_dir),
            "--region",
            "minimap",
            "--limit",
            "1",
            "--save-samples",
        ]
    )

    output = capsys.readouterr().out
    assert "ROI: minimap x=1 y=0 width=1 height=1" in output
    assert "Frames loaded: 1" in output

    events = _read_run_events(tmp_path)

    assert events[0]["data"]["region_source"] == "config"
    assert events[0]["data"]["region"] == {
        "name": "minimap",
        "x": 1,
        "y": 0,
        "width": 1,
        "height": 1,
    }
    assert events[1]["event"] == "roi_extracted"
    assert events[1]["data"]["region_source"] == "config"
    assert events[1]["data"]["region_name"] == "minimap"
    assert events[1]["data"]["frame_path"] == str(frames_dir / "processed_frame_000001.ppm")

    sample_files = list((tmp_path / "runs").glob("*/artifacts/roi/minimap_000001.ppm"))
    assert len(sample_files) == 1
    assert sample_files[0].read_bytes() == b"P6\n1 1\n255\n\x04\x05\x06"


def test_roi_smoke_cli_fails_for_unknown_configured_region(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir()
    _write_ppm(
        frames_dir / "processed_frame_000001.ppm",
        width=1,
        height=1,
        payload=b"\x01\x02\x03",
    )
    config_file = tmp_path / "config.toml"
    config_file.write_text("", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit, match="Unknown ROI region preset: missing"):
        main(
            [
                "--config",
                str(config_file),
                "roi-smoke",
                "--frames-dir",
                str(frames_dir),
                "--region",
                "missing",
                "--limit",
                "1",
            ]
        )


def test_roi_smoke_cli_rejects_ambiguous_manual_and_configured_region(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir()
    _write_ppm(
        frames_dir / "processed_frame_000001.ppm",
        width=1,
        height=1,
        payload=b"\x01\x02\x03",
    )
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        """
[regions.minimap]
x = 0
y = 0
width = 1
height = 1
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit, match="cannot be combined with manual region arguments"):
        main(
            [
                "--config",
                str(config_file),
                "roi-smoke",
                "--frames-dir",
                str(frames_dir),
                "--region",
                "minimap",
                "--x",
                "0",
                "--limit",
                "1",
            ]
        )


def _processed_frame(
    width: int,
    height: int,
    data: bytes,
    pixel_format: str = "RGB",
) -> ProcessedFrame:
    return ProcessedFrame(
        frame_id=42,
        width=width,
        height=height,
        source_frame_width=width,
        source_frame_height=height,
        source="test",
        pixel_format=pixel_format,
        data=data,
    )


def _write_ppm(path: Path, width: int, height: int, payload: bytes) -> None:
    path.write_bytes(f"P6\n{width} {height}\n255\n".encode("ascii") + payload)


def _read_run_events(tmp_path: Path) -> list[dict[str, Any]]:
    event_files = list((tmp_path / "runs").glob("*/logs/events.jsonl"))
    assert len(event_files) == 1
    return [
        json.loads(line)
        for line in event_files[0].read_text(encoding="utf-8").splitlines()
    ]
