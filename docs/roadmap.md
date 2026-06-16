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
