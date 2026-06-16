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

FASE 0 - Foundation

The current goal is to create a clean, testable, versioned project foundation before
adding screen capture, OCR, vision models, LLM calls, or execution modules.

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

Current configuration is limited to logging, runtime output paths, future capture
settings, and future model-routing settings. Capture and model routing are disabled
by default and are not implemented in the current phase.
