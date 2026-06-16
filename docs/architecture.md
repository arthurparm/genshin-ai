# Architecture

## Objective

This document describes the intended architecture for the Genshin AI research agent.

The system must be modular, observable, testable, and safe. It should use
screen-based perception, structured state modeling, hierarchical planning,
deterministic execution, logs, replay, and metrics.

## High-level Pipeline

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

## Module Boundaries

### 1. Capture

Responsible for acquiring frames from the screen or from recorded sessions.

Future responsibilities:

- capture current screen
- measure capture FPS
- resize frames
- save sample frames
- support replay input

### 2. Perception

Responsible for converting frames into observations.

Future responsibilities:

- HUD detection
- OCR
- UI state classification
- enemy detection
- interactable detection
- minimap parsing
- confidence scoring

### 3. State

Responsible for converting observations into a canonical state.

Future responsibilities:

- WorldState model
- temporal state history
- state confidence
- change detection
- inconsistency detection

### 4. Planning

Responsible for deciding what should happen next.

Future responsibilities:

- behavior trees
- finite state machines
- task planner
- LLM strategic planner
- fallback policies
- JSON schema validation

### 5. Execution

Responsible for executing bounded actions.

Future responsibilities:

- action queue
- timeouts
- cancellation
- post-action validation
- safe executor abstraction
- simulation/mock executor

### 6. Evaluation

Responsible for proving whether the agent is improving.

Future responsibilities:

- metrics
- run reports
- replays
- task success rate
- failure classification
- latency measurement

## LLM Usage Policy

LLMs must be used for strategy and high-level planning only.

The LLM should receive structured state, not raw frames, by default.

The LLM should return validated structured decisions, preferably JSON.

The LLM must not directly decide individual key presses every frame.

## Safety Boundary

This project must avoid invasive techniques, including:

- memory reading
- bypassing anti-cheat systems
- reverse engineering protected internals
- modifying the game client
- exploiting vulnerabilities

The project must rely on screen-based perception, OCR, controlled execution, logs,
and safe experimentation.

## Initial Target

The first technical milestone after foundation is not gameplay.

The first milestone is:

1. Capture screen
2. Resize frame
3. Measure FPS
4. Save sample frames
5. Emit structured logs
6. Validate the loop through tests
