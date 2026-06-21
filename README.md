# genshin-ai

Research project for building a modular AI agent capable of playing selected parts of
Genshin Impact through computer vision, structured world-state modeling,
hierarchical planning, deterministic execution, logs, replay, and incremental
evaluation.

## Objective

The goal is to build a safe, controlled, research-oriented agent architecture that
observes the game screen, extracts structured state, plans high-level actions, and
executes bounded low-level actions through deterministic modules.

The project does not aim to modify the game client, read process memory, bypass
anti-cheat systems, exploit vulnerabilities, or manipulate internal game state.

## Core Principle

GPT or any LLM must act as a strategic planner, not as a frame-by-frame controller.

The system should follow this high-level pipeline:

```text
Screen Capture
    |
Frame Preprocessor
    |
Computer Vision Layer
    |
OCR Layer
    |
HUD Parser
    |
World State Builder
    |
Memory / State Store
    |
Behavior Tree / State Machine
    |
GPT Strategic Planner
    |
Task Planner
    |
Action Queue
    |
Input Executor
    |
Monitor / Supervisor
    |
Logs / Replay / Evaluation
```

## Current Phase

FASE 2.2 - ROI Batch Extraction Manifest

The current goal is to create audit-ready ROI manifests from processed replay
frames before adding OCR, semantic vision, LLM calls, or execution modules.

## Hardware Target

Primary machine:

- Intel i9-13900F
- 64 GB RAM
- RTX 4060 Ti 16 GB
- Windows

Secondary machine:

- Mac Mini M4
- 24 GB RAM

Additional resources:

- OmniRouter for model routing
- Local and remote model execution
- Internal frame downscaling for efficient perception

## Initial Development Priorities

1. Project structure
2. Logging and configuration
3. Screen capture and FPS metrics
4. Frame preprocessing and resize
5. Structured world state
6. Basic perception modules
7. Deterministic execution
8. Behavior tree
9. Strategic GPT planner
10. Evaluation and replay

## Safety and Scope

This project must remain within safe research boundaries:

- No memory reading
- No reverse engineering of protected internals
- No anti-cheat bypass
- No exploitation
- No invasive manipulation of the game process

The intended approach is visual perception, OCR, structured state, deterministic
execution, logs, and controlled experimentation.

## Development

Install dependencies:

```powershell
pip install -e ".[dev]"
```

Run tests:

```powershell
python -m pytest
```

Run CLI sanity check:

```powershell
python -m genshin_ai.cli
```

Run CLI sanity check with an explicit config file:

```powershell
python -m genshin_ai.cli --config config.example.toml
```

Run a bounded mock capture smoke test:

```powershell
python -m genshin_ai.cli capture-smoke
python -m genshin_ai.cli --config config.example.toml capture-smoke
```

Install the optional real screen-capture backend:

```powershell
pip install -e ".[dev,capture]"
```

Install the optional optimized image preprocessing backend:

```powershell
pip install -e ".[dev,capture,image]"
```

Run a bounded real screen-capture smoke test:

```powershell
python -m genshin_ai.cli screen-capture-smoke --frames 5
python -m genshin_ai.cli screen-capture-smoke --frames 5 --save-samples
python -m genshin_ai.cli screen-capture-smoke --frames 5 --preprocess --save-samples
python -m genshin_ai.cli screen-capture-smoke --frames 5 --preprocess --preprocess-backend pillow
```

Run an operational capture benchmark:

```powershell
python -m genshin_ai.cli capture-benchmark --frames 30
python -m genshin_ai.cli capture-benchmark --frames 30 --preprocess
python -m genshin_ai.cli capture-benchmark --frames 30 --preprocess --save-every 10
python -m genshin_ai.cli capture-benchmark --frames 30 --preprocess --preprocess-backend pillow
```

Run a replay smoke test from processed PPM frames:

```powershell
python -m genshin_ai.cli replay-smoke --frames-dir runs/<run_id>/captures
python -m genshin_ai.cli replay-smoke --frames-dir runs/<run_id>/captures --limit 5
```

Run a region-of-interest smoke test from processed PPM replay frames:

```powershell
python -m genshin_ai.cli roi-smoke --frames-dir runs/<run_id>/captures --x 0 --y 0 --width 100 --height 100 --name test_region --limit 1
python -m genshin_ai.cli roi-smoke --frames-dir runs/<run_id>/captures --x 0 --y 0 --width 100 --height 100 --name test_region --limit 1 --save-samples
python -m genshin_ai.cli --config config.example.toml roi-smoke --frames-dir runs/<run_id>/captures --region minimap --limit 1
```

Run ROI batch extraction from configured presets and write an audit manifest:

```powershell
python -m genshin_ai.cli --config config.example.toml roi-batch --frames-dir runs/<run_id>/captures --limit 10 --save-samples
python -m genshin_ai.cli --config config.example.toml roi-batch --frames-dir runs/<run_id>/captures --regions minimap,interaction_prompt --limit 10 --save-samples
```

The CLI creates one run-scoped directory per execution:

```text
runs/<run_id>/
  metadata.json
  logs/events.jsonl
  captures/
  replays/
  artifacts/
```

## Configuration

Configuration is loaded from safe defaults unless a TOML file is provided with
`--config`.

Use `config.example.toml` as the versioned reference. Local machine-specific config
should be stored in `config.local.toml`, which is ignored by Git.

Current configuration covers logging, runtime output paths, future capture settings,
future model-routing settings, and named ROI presets. Capture and model routing are
disabled by default and are not implemented in the current phase.

ROI presets are declared under `[regions.<name>]` and use processed-frame
coordinates:

```toml
[regions.minimap]
x = 1120
y = 40
width = 140
height = 140
```

Region names are restricted to letters, numbers, underscores, and hyphens so logs
and saved ROI samples can use the same name safely.

The `capture-smoke` command uses a mock capture source. It does not capture the real
screen and does not interact with Genshin Impact.

The `screen-capture-smoke` command uses the optional `mss` backend to capture the
primary monitor. It is for manual observability testing only; it does not inspect
game memory, automate input, or require Genshin Impact to be open.

The real screen-capture backend keeps one `mss` capture context open for the
duration of the smoke test or benchmark run. This keeps per-frame measurements
focused on `grab()` latency instead of repeatedly measuring `mss` setup and
teardown overhead.

When `--preprocess` is enabled, captured BGRA frames are converted to RGB and
resized to `capture.process_width` x `capture.process_height` from the loaded
configuration. Processed samples are written as PPM files under the run captures
directory when `--save-samples` is also enabled.

The default preprocessing backend is `python`, which has no optional image
dependency. The optional `pillow` backend requires the `image` extra and is intended
for benchmarked preprocessing performance comparisons before OCR or semantic vision
is added.

The `capture-benchmark` command writes `capture_benchmark.json` under the run
artifacts directory with FPS, capture latency, preprocessing latency, failures, and
sample counts. When preprocessing is enabled, the report also records the
`preprocess_backend` used for the run. Use `average_capture_ms`,
`average_total_frame_ms`, and `actual_fps` to compare capture backend changes
before and after optimization commits.

The `replay-smoke` command reads processed binary PPM (`P6`) frames from a
directory and returns deterministic RGB `ProcessedFrame` objects for future
perception tests. It emits replay events to the run JSONL log and does not capture
the screen, perform OCR, run semantic vision, automate input, or call models.
Each `replay_frame_loaded` event includes frame metadata and `frame_path` for
auditability.

The `roi-smoke` command reads the same processed PPM replay input and extracts a
bounded RGB region either by explicit pixel coordinates or by a configured
`--region` preset. It rejects ambiguous calls that combine preset mode with manual
coordinates. It emits `roi_smoke_started`, `roi_extracted`, optional
`roi_sample_saved`, and `roi_smoke_finished` events. Each ROI event includes
`region_source` (`manual` or `config`), region metadata, `source_frame_id` where
applicable, and `frame_path` for extracted frames. Saved ROI samples are written as
PPM files under `runs/<run_id>/artifacts/roi/`. This command only prepares
structural perception input for future OCR, HUD parsing, minimap parsing, and
evaluation; it does not interpret image content.

The `roi-batch` command extracts one or more configured ROI presets for every
loaded replay frame and saves `runs/<run_id>/artifacts/roi_manifest.json`. If
`--regions` is omitted, all configured presets are used. If `--save-samples` is
provided, extracted ROI samples are saved under `runs/<run_id>/artifacts/roi/`
and each manifest entry records its `sample_path`. The command emits
`roi_batch_started`, `roi_batch_region_extracted`,
`roi_batch_manifest_saved`, and `roi_batch_finished` events. Each extracted
entry records `frame_path`, `region_name`, `region_source`, coordinates, source
frame dimensions, pixel format, and optional sample path. This remains a
structural replay/evaluation primitive only; it does not run OCR, semantic
vision, or gameplay automation.

A typical manual replay flow is:

```powershell
python -m genshin_ai.cli screen-capture-smoke --frames 5 --preprocess --preprocess-backend pillow --save-samples
python -m genshin_ai.cli replay-smoke --frames-dir runs/<run_id>/captures --limit 5
python -m genshin_ai.cli roi-smoke --frames-dir runs/<run_id>/captures --x 0 --y 0 --width 100 --height 100 --name test_region --limit 1 --save-samples
python -m genshin_ai.cli --config config.example.toml roi-smoke --frames-dir runs/<run_id>/captures --region minimap --limit 1 --save-samples
python -m genshin_ai.cli --config config.example.toml roi-batch --frames-dir runs/<run_id>/captures --regions minimap,interaction_prompt --limit 5 --save-samples
```
