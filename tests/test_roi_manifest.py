import json
from pathlib import Path
from typing import Any

import pytest

from genshin_ai.cli import main
from genshin_ai.perception.regions import RegionSpec
from genshin_ai.perception.roi_manifest import (
    RoiManifest,
    RoiManifestEntry,
    extract_roi_batch,
    save_roi_manifest,
)


def test_roi_manifest_entry_to_dict() -> None:
    entry = RoiManifestEntry(
        frame_id=1,
        frame_path="frames/processed_frame_000001.ppm",
        region_name="minimap",
        region_source="config",
        x=0,
        y=1,
        width=2,
        height=3,
        source_frame_width=10,
        source_frame_height=20,
        pixel_format="RGB",
        sample_path="runs/run/artifacts/roi/minimap_000001.ppm",
    )

    assert entry.to_dict() == {
        "frame_id": 1,
        "frame_path": "frames/processed_frame_000001.ppm",
        "region_name": "minimap",
        "region_source": "config",
        "x": 0,
        "y": 1,
        "width": 2,
        "height": 3,
        "source_frame_width": 10,
        "source_frame_height": 20,
        "pixel_format": "RGB",
        "sample_path": "runs/run/artifacts/roi/minimap_000001.ppm",
    }


def test_roi_manifest_to_dict() -> None:
    region = RegionSpec(name="minimap", x=0, y=0, width=1, height=1)
    entry = RoiManifestEntry(
        frame_id=1,
        frame_path="frames/processed_frame_000001.ppm",
        region_name="minimap",
        region_source="config",
        x=0,
        y=0,
        width=1,
        height=1,
        source_frame_width=2,
        source_frame_height=2,
        pixel_format="RGB",
        sample_path=None,
    )
    manifest = RoiManifest(
        run_id="run-1",
        frames_dir="frames",
        regions=(region,),
        entries=(entry,),
    )

    assert manifest.to_dict() == {
        "run_id": "run-1",
        "frames_dir": "frames",
        "regions": [{"name": "minimap", "x": 0, "y": 0, "width": 1, "height": 1}],
        "entries": [entry.to_dict()],
    }


def test_save_roi_manifest_writes_valid_json(tmp_path: Path) -> None:
    manifest = RoiManifest(
        run_id="run-1",
        frames_dir="frames",
        regions=(RegionSpec(name="minimap", x=0, y=0, width=1, height=1),),
        entries=(),
    )

    output_path = save_roi_manifest(manifest, tmp_path / "nested" / "roi_manifest.json")

    assert output_path == tmp_path / "nested" / "roi_manifest.json"
    assert json.loads(output_path.read_text(encoding="utf-8")) == manifest.to_dict()


def test_extract_roi_batch_with_two_frames_and_two_regions_creates_four_entries(
    tmp_path: Path,
) -> None:
    frames_dir = tmp_path / "frames"
    _write_replay_frames(frames_dir)
    regions = (
        RegionSpec(name="left", x=0, y=0, width=1, height=1),
        RegionSpec(name="right", x=1, y=0, width=1, height=1),
    )

    manifest = extract_roi_batch(
        frames_dir=frames_dir,
        regions=regions,
        run_id="run-1",
        artifacts_dir=tmp_path / "artifacts",
        limit=2,
    )

    assert len(manifest.entries) == 4
    assert [entry.region_name for entry in manifest.entries] == [
        "left",
        "right",
        "left",
        "right",
    ]
    assert {entry.frame_path for entry in manifest.entries} == {
        str(frames_dir / "processed_frame_000001.ppm"),
        str(frames_dir / "processed_frame_000002.ppm"),
    }


def test_extract_roi_batch_with_save_samples_writes_ppm_files(tmp_path: Path) -> None:
    frames_dir = tmp_path / "frames"
    _write_ppm(
        frames_dir / "processed_frame_000001.ppm",
        width=2,
        height=1,
        payload=b"\x01\x02\x03\x04\x05\x06",
    )

    manifest = extract_roi_batch(
        frames_dir=frames_dir,
        regions=(RegionSpec(name="right", x=1, y=0, width=1, height=1),),
        run_id="run-1",
        artifacts_dir=tmp_path / "artifacts",
        limit=1,
        save_samples=True,
    )

    sample_path = tmp_path / "artifacts" / "roi" / "right_000001.ppm"
    assert manifest.entries[0].sample_path == str(sample_path)
    assert sample_path.read_bytes() == b"P6\n1 1\n255\n\x04\x05\x06"


def test_extract_roi_batch_finishes_when_replay_ends_after_loaded_frames(
    tmp_path: Path,
) -> None:
    frames_dir = tmp_path / "frames"
    _write_ppm(
        frames_dir / "processed_frame_000001.ppm",
        width=1,
        height=1,
        payload=b"\x01\x02\x03",
    )

    manifest = extract_roi_batch(
        frames_dir=frames_dir,
        regions=(RegionSpec(name="single", x=0, y=0, width=1, height=1),),
        run_id="run-1",
        artifacts_dir=tmp_path / "artifacts",
        limit=5,
    )

    assert len(manifest.entries) == 1


def test_extract_roi_batch_rejects_non_positive_limit(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="limit must be positive"):
        extract_roi_batch(
            frames_dir=tmp_path,
            regions=(RegionSpec(name="single", x=0, y=0, width=1, height=1),),
            run_id="run-1",
            artifacts_dir=tmp_path / "artifacts",
            limit=0,
        )


def test_roi_batch_cli_uses_all_configured_presets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    frames_dir = tmp_path / "frames"
    _write_ppm(
        frames_dir / "processed_frame_000001.ppm",
        width=2,
        height=1,
        payload=b"\x01\x02\x03\x04\x05\x06",
    )
    config_file = _write_config(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(
        [
            "--config",
            str(config_file),
            "roi-batch",
            "--frames-dir",
            str(frames_dir),
            "--limit",
            "1",
            "--save-samples",
        ]
    )

    output = capsys.readouterr().out
    assert "Manifest entries: 2" in output

    manifest = _read_single_manifest(tmp_path)
    assert [entry["region_name"] for entry in manifest["entries"]] == [
        "minimap",
        "interaction_prompt",
    ]
    assert len(list((tmp_path / "runs").glob("*/artifacts/roi/*.ppm"))) == 2


def test_roi_batch_cli_uses_selected_region(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frames_dir = tmp_path / "frames"
    _write_ppm(
        frames_dir / "processed_frame_000001.ppm",
        width=2,
        height=1,
        payload=b"\x01\x02\x03\x04\x05\x06",
    )
    config_file = _write_config(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(
        [
            "--config",
            str(config_file),
            "roi-batch",
            "--frames-dir",
            str(frames_dir),
            "--regions",
            "minimap",
            "--limit",
            "1",
        ]
    )

    manifest = _read_single_manifest(tmp_path)
    assert [entry["region_name"] for entry in manifest["entries"]] == ["minimap"]


def test_roi_batch_cli_fails_for_unknown_preset(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frames_dir = tmp_path / "frames"
    _write_ppm(
        frames_dir / "processed_frame_000001.ppm",
        width=1,
        height=1,
        payload=b"\x01\x02\x03",
    )
    config_file = _write_config(tmp_path)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit, match="Unknown ROI region preset: missing"):
        main(
            [
                "--config",
                str(config_file),
                "roi-batch",
                "--frames-dir",
                str(frames_dir),
                "--regions",
                "missing",
            ]
        )


def test_roi_batch_cli_fails_when_no_presets_are_configured(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frames_dir = tmp_path / "frames"
    _write_ppm(
        frames_dir / "processed_frame_000001.ppm",
        width=1,
        height=1,
        payload=b"\x01\x02\x03",
    )
    config_file = tmp_path / "config.toml"
    config_file.write_text("", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit, match="requires at least one configured ROI preset"):
        main(
            [
                "--config",
                str(config_file),
                "roi-batch",
                "--frames-dir",
                str(frames_dir),
            ]
        )


def test_roi_batch_events_include_frame_path_and_manifest_saved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frames_dir = tmp_path / "frames"
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

    main(
        [
            "--config",
            str(config_file),
            "roi-batch",
            "--frames-dir",
            str(frames_dir),
            "--regions",
            "minimap",
            "--limit",
            "1",
        ]
    )

    events = _read_run_events(tmp_path)
    extracted_event = next(
        event for event in events if event["event"] == "roi_batch_region_extracted"
    )
    saved_event = next(event for event in events if event["event"] == "roi_batch_manifest_saved")

    assert extracted_event["data"]["frame_path"] == str(frames_dir / "processed_frame_000001.ppm")
    assert extracted_event["data"]["region_source"] == "config"
    assert saved_event["data"]["entries"] == 1


def _write_config(tmp_path: Path) -> Path:
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        """
[regions.minimap]
x = 0
y = 0
width = 1
height = 1

[regions.interaction_prompt]
x = 1
y = 0
width = 1
height = 1
""".strip(),
        encoding="utf-8",
    )
    return config_file


def _write_replay_frames(frames_dir: Path) -> None:
    _write_ppm(
        frames_dir / "processed_frame_000001.ppm",
        width=2,
        height=1,
        payload=b"\x01\x02\x03\x04\x05\x06",
    )
    _write_ppm(
        frames_dir / "processed_frame_000002.ppm",
        width=2,
        height=1,
        payload=b"\x07\x08\x09\x0a\x0b\x0c",
    )


def _write_ppm(path: Path, width: int, height: int, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(f"P6\n{width} {height}\n255\n".encode("ascii") + payload)


def _read_single_manifest(tmp_path: Path) -> dict[str, Any]:
    manifest_files = list((tmp_path / "runs").glob("*/artifacts/roi_manifest.json"))
    assert len(manifest_files) == 1
    payload: Any = json.loads(manifest_files[0].read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _read_run_events(tmp_path: Path) -> list[dict[str, Any]]:
    event_files = list((tmp_path / "runs").glob("*/logs/events.jsonl"))
    assert len(event_files) == 1
    return [
        json.loads(line)
        for line in event_files[0].read_text(encoding="utf-8").splitlines()
    ]
