# Roadmap

## FASE 0 - Foundation

Goal: establish a clean, versioned, testable project baseline.

Tasks:

- initialize Git repository
- create Python package structure
- add README
- add AGENTS guide
- add architecture document
- add roadmap
- add pytest
- add sanity test

Exit criteria:

- `git status` works
- `python -m pytest` passes
- project imports successfully
- no gameplay automation exists

## FASE 0.1 - Structured Logging

Goal: establish structured logs before any capture, perception, execution, or planning module.

Tasks:

- create RuntimeContext
- create JSONL event logger
- emit CLI sanity event
- create log directory automatically
- add tests for logging and runtime metadata

Exit criteria:

- `python -m pytest` passes
- `python -m genshin_ai.cli` creates one JSONL log file
- log entries include run_id, timestamp, module, event, level, phase, and data
- no screen capture exists
- no input automation exists
- no LLM call exists

## FASE 0.2 - Typed Configuration

Goal: establish typed, safe, testable configuration before capture, perception, execution, or
planning modules.

Tasks:

- create typed immutable config dataclasses
- load defaults when no config path is provided
- load TOML overrides from an optional config file
- reject unknown sections and keys
- add config data to CLI sanity logs
- add tests for defaults, overrides, and invalid config

Exit criteria:

- `python -m pytest` passes
- `python -m genshin_ai.cli` works with defaults
- `python -m genshin_ai.cli --config config.example.toml` works
- CLI logs include the config source and loaded config
- no screen capture exists
- no input automation exists
- no LLM call exists

## FASE 0.3 - Run Session and Artifact Directories

Goal: group runtime logs and future artifacts under one run-scoped directory.

Tasks:

- create RunSession
- create run-scoped directories from run_id
- write metadata.json for each run
- route CLI JSONL logs to the run session logs directory
- add tests for session directory creation and metadata

Exit criteria:

- `python -m pytest` passes
- `python -m genshin_ai.cli` creates `runs/<run_id>/`
- each run directory contains metadata, logs, captures, replays, and artifacts paths
- CLI logs are written to `runs/<run_id>/logs/events.jsonl`
- no screen capture exists
- no input automation exists
- no LLM call exists

## FASE 1 - Capture and Observability

Goal: capture frames and measure performance without acting on the game.

## FASE 1.0 - Capture Abstraction and Mock Metrics

Goal: prove the capture loop contract with a mock source before adding real screen capture.

Tasks:

- define CapturedFrame
- define CaptureSource
- create MockCaptureSource
- create CaptureMetrics
- add bounded capture smoke test
- emit capture smoke events to JSONL logs
- add CLI command `capture-smoke`

Exit criteria:

- `python -m pytest` passes
- `python -m genshin_ai.cli capture-smoke` creates capture events
- mock frame metadata includes source, frame id, dimensions, and timestamp
- capture metrics include frames captured, target FPS, actual FPS, and failures
- no real screen capture exists
- no input automation exists
- no LLM call exists

## FASE 1.1 - Real Screen Capture Backend

Goal: add an isolated real screen-capture backend for manual observability smoke tests.

Tasks:

- add optional `mss` capture dependency
- isolate real capture behind CaptureSource
- add screen-capture smoke command
- save optional PPM frame samples
- log real capture smoke events
- keep unit tests independent from real monitors

Exit criteria:

- `python -m pytest` passes
- `python -m genshin_ai.cli capture-smoke` still works without `mss`
- `python -m genshin_ai.cli screen-capture-smoke --frames 5` works when `mss` is installed
- `--save-samples` writes PPM files under `runs/<run_id>/captures/`
- no OCR exists
- no input automation exists
- no LLM call exists

## FASE 1.2 - Frame Preprocessing and Resize Pipeline

Goal: convert captured BGRA frames to resized RGB frames before OCR or vision models exist.

Tasks:

- define ProcessedFrame
- convert BGRA to RGB
- resize frames with nearest-neighbor
- save processed PPM samples
- integrate `--preprocess` into `screen-capture-smoke`
- log `frame_preprocessed` events
- add unit tests independent from real capture

Exit criteria:

- `python -m pytest` passes
- `screen-capture-smoke --preprocess --save-samples` saves processed PPM files
- processed frames use `capture.process_width` and `capture.process_height`
- events include `frame_preprocessed`
- no OCR exists
- no semantic vision exists
- no input automation exists
- no LLM call exists

## FASE 1.3 - Capture Benchmark Reporting

Goal: measure real capture and preprocessing performance before adding OCR or vision models.

Tasks:

- add CaptureBenchmarkReport
- benchmark capture latency
- benchmark preprocessing latency
- measure actual FPS
- save benchmark JSON reports
- optionally save benchmark samples
- log benchmark start, frame, and finish events

Exit criteria:

- `python -m pytest` passes
- `capture-benchmark --frames 30` writes `capture_benchmark.json`
- `capture-benchmark --frames 30 --preprocess` reports preprocessing latency
- reports include FPS, average capture ms, average preprocess ms, failures, and samples saved
- no OCR exists
- no semantic vision exists
- no input automation exists
- no LLM call exists

## FASE 1.4 - Optional Optimized Preprocessing Backend

Goal: add an optional optimized BGRA-to-RGB resize backend before OCR or semantic vision.

Tasks:

- add optional Pillow dependency under the `image` extra
- keep the Python preprocessing backend as the default
- add backend selection to config, smoke tests, and benchmark CLI
- record the preprocessing backend in logs and benchmark reports
- keep unit tests independent from real monitors and optional Pillow availability

Exit criteria:

- `python -m pytest` passes without installing the `image` extra
- `capture-benchmark --frames 30 --preprocess` works with backend `python`
- `capture-benchmark --frames 30 --preprocess --preprocess-backend pillow` works when Pillow is installed
- `capture_benchmark.json` includes `preprocess_backend`
- no OCR exists
- no semantic vision exists
- no input automation exists
- no LLM call exists

## FASE 1.5 - Persistent Screen Capture Context

Goal: reduce per-frame capture overhead before adding OCR or semantic vision.

Tasks:

- keep one `mss` capture context open per `MssScreenCaptureSource` instance
- cache the selected monitor during initialization
- make real capture smoke tests and benchmarks close the capture resource explicitly
- add unit tests with fake `mss` objects instead of real monitors

Exit criteria:

- `python -m pytest` passes
- `capture_frame()` calls `grab()` without recreating the `mss` context per frame
- `capture-benchmark` can compare `average_capture_ms` before and after the change
- no OCR exists
- no semantic vision exists
- no input automation exists
- no LLM call exists

## FASE 1.6 - Processed Frame Replay Source

Goal: replay processed RGB frames from saved PPM files before adding OCR or semantic vision.

Tasks:

- add a replay source for processed binary PPM frames
- parse PPM P6 headers and RGB payloads with explicit validation
- add a `replay-smoke` CLI command
- emit replay start, frame-loaded, and finish events
- keep tests independent from real screen capture

Exit criteria:

- `python -m pytest` passes
- `replay-smoke --frames-dir <dir>` loads valid processed PPM frames
- replay frames are deterministic and ordered by filename
- invalid replay inputs fail with clear errors
- no OCR exists
- no semantic vision exists
- no input automation exists
- no LLM call exists

## FASE 1.7 - Replay Auditability Hardening

Goal: harden processed-frame replay before using it as a regression input for OCR,
HUD parsing, or visual perception.

Tasks:

- make replay frame loading transactional when PPM parsing fails
- expose the loaded frame path with the replay frame result
- use a typed end-of-sequence error instead of message matching
- include `frame_path` in `replay_frame_loaded` events
- normalize replay frame file read failures as `ReplayFrameError`

Exit criteria:

- `python -m pytest` passes
- `ruff check .` passes
- `mypy src tests` passes
- invalid replay frames do not advance the replay sequence
- replay end-of-sequence is represented by `ReplayEndOfSequenceError`
- `replay_frame_loaded` events include `frame_path`
- file read failures are wrapped as `ReplayFrameError`
- no OCR exists
- no semantic vision exists
- no input automation exists
- no LLM call exists

Tasks:

- implement screen capture abstraction
- implement frame resize
- measure capture FPS
- save sample frames
- create capture session output directory

Exit criteria:

- capture loop runs
- FPS is measured
- frames can be saved
- logs are generated
- no input automation exists

## FASE 2 - Basic Perception

Goal: extract basic information from frames.

## FASE 2.0 - ROI Extraction and Perception Observation Contracts

Goal: create a minimal structural perception layer that extracts explicit RGB
regions from processed replay frames before OCR or semantic vision exists.

Tasks:

- define immutable `RegionSpec`
- define immutable `RegionFrame`
- validate ROI coordinates and RGB frame contracts
- extract ROI bytes from processed `RGB` frames
- save ROI samples as PPM files
- add `roi-smoke` CLI command backed by processed-frame replay
- emit ROI events with source `frame_path` for auditability
- keep unit tests independent from real screen capture

Exit criteria:

- `python -m pytest` passes
- `ruff check .` passes
- `mypy src tests` passes
- `roi-smoke --frames-dir <dir> --x 0 --y 0 --width 1 --height 1 --name test --limit 1`
  works with valid processed PPM input
- ROI samples can be saved under `runs/<run_id>/artifacts/roi/`
- ROI outside frame bounds fails with a clear error
- `roi_extracted` events include region metadata, `source_frame_id`, and `frame_path`
- no OCR exists
- no semantic vision exists
- no input automation exists
- no LLM call exists

## FASE 2.1 - Configurable ROI Presets

Goal: make ROI extraction reproducible through named, validated presets before
OCR, HUD parsing, or minimap parsing exists.

Tasks:

- add immutable `RegionConfig` presets to typed configuration
- load `[regions.<name>]` tables from TOML
- reuse `RegionSpec` validation for configured presets
- restrict region names to safe log and filename identifiers
- support `roi-smoke --region <preset>` alongside manual coordinates
- include `region_source` and region metadata in ROI events
- reject unknown presets and ambiguous manual/preset CLI input

Exit criteria:

- `python -m pytest` passes
- `ruff check .` passes
- `mypy src tests` passes
- manual `roi-smoke` coordinate mode still works
- configured `roi-smoke --region minimap` works with valid processed PPM input
- invalid region names and invalid coordinates fail with clear errors
- no OCR exists
- no semantic vision exists
- no input automation exists
- no LLM call exists

## FASE 2.2 - ROI Batch Extraction Manifest

Goal: extract configured ROI presets across processed replay frames and produce
an audit-ready JSON manifest before OCR, HUD parsing, or minimap parsing exists.

Tasks:

- define immutable `RoiManifestEntry`
- define immutable `RoiManifest`
- serialize ROI manifests to deterministic JSON
- extract every requested ROI preset from each replay frame
- support bounded frame limits and early replay end after loaded frames
- optionally save ROI sample PPM files under run artifacts
- add `roi-batch` CLI command for all presets or selected presets
- emit batch start, per-region extraction, manifest-saved, and finish events
- keep tests independent from real screen capture

Exit criteria:

- `python -m pytest` passes
- `ruff check .` passes
- `mypy src tests` passes
- `roi-batch --frames-dir <dir>` works with configured presets
- `roi-batch --regions minimap` selects one configured preset
- missing presets and empty preset config fail with clear errors
- manifest contains one entry per loaded frame per region
- sample paths are recorded when `--save-samples` is used
- extracted events include `frame_path`, `region_name`, and `region_source`
- no OCR exists
- no semantic vision exists
- no input automation exists
- no LLM call exists

Tasks:

- detect screen mode
- classify UI state
- add OCR baseline
- detect HUD regions
- store observations with confidence

Exit criteria:

- perception produces structured observations
- confidence is explicit
- failures are logged
- tests cover parser logic

## FASE 3 - Canonical World State

Goal: transform observations into state.

Tasks:

- define WorldState
- define Observation
- add temporal history
- add state confidence
- detect state changes

Exit criteria:

- WorldState can be generated
- state transitions are logged
- inconsistent state can be detected

## FASE 4 - Safe Executor

Goal: define bounded action execution with safety checks.

Tasks:

- define action model
- define action queue
- define mock executor
- add timeout and cancellation
- add post-action validation hooks

Exit criteria:

- mock executor works
- action queue is testable
- no real gameplay action is required for tests

## FASE 5 - Behavior Tree / State Machine

Goal: implement deterministic task logic.

Tasks:

- create behavior tree primitives
- create task nodes
- create fallback nodes
- create validation nodes
- implement simple non-invasive tasks

Exit criteria:

- tasks are composable
- failures are recoverable
- execution is observable

## FASE 6 - GPT Strategic Planner

Goal: add LLM only as a strategic planner.

Tasks:

- define planner input schema
- define planner output schema
- add JSON validation
- add local/remote model routing
- add fallback behavior

Exit criteria:

- planner returns structured decisions
- invalid LLM output is rejected
- fallback works
- LLM is not used frame by frame

## FASE 7 - Multi-agent Layer

Goal: split planning responsibilities.

Agents:

- Strategic Agent
- Quest Agent
- Navigation Agent
- Combat Agent
- UI Agent
- Supervisor Agent
- Memory Agent

Exit criteria:

- agents communicate through structured state
- responsibilities are isolated
- supervisor can reject unsafe actions

## FASE 8 - Evaluation

Goal: measure whether the system is improving.

Tasks:

- define metrics
- create run reports
- classify failures
- measure latency
- measure success rate
- support replay analysis

Exit criteria:

- runs are comparable
- regressions are visible
- failures can be inspected

## FASE 9 - Expansion

Goal: gradually increase task complexity.

Possible tasks:

- known farm route
- simple teleport flow
- UI navigation
- basic collection
- restricted combat scenario
- simple domain routine

Exit criteria:

- each task has metrics
- each task has replay evidence
- each task has bounded scope
