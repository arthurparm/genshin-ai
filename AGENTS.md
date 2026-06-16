# Agent Engineering Guide

This document defines the technical behavior expected from AI assistants and
developers working on this repository.

## Project Mission

Build a modular research agent for Genshin Impact based on:

- computer vision
- OCR
- structured world state
- hierarchical planning
- deterministic executors
- behavior trees
- logs
- replay
- evaluation metrics
- LLM-based strategic planning

## Non-goals

This project must not include:

- process memory reading
- anti-cheat bypass
- reverse engineering of protected game internals
- exploit development
- invasive game-client manipulation
- automation techniques designed to evade detection

If a technical path depends on those methods, reject it and propose a safe
alternative.

## Architectural Rule

LLMs must not control the game frame by frame.

Correct:

```text
LLM -> chooses objective or strategy
Behavior Tree -> decomposes task
Executor -> performs bounded action
Supervisor -> validates result
```

Incorrect:

```text
Frame -> LLM -> key press
Frame -> LLM -> key press
Frame -> LLM -> key press
```

## Commit Review Protocol

Every commit must be evaluated by:

- what changed
- what improved
- what worsened
- risks introduced
- technical debt added or removed
- impact on architecture
- impact on final agent objective
- acceptance or rejection decision
- next recommended commit

## Engineering Priorities

In order:

1. Observability
2. Reproducibility
3. Safety
4. Modularity
5. Testability
6. Performance
7. Scalability
8. Intelligence

Do not add intelligence before observability.

Do not add automation before state validation.

Do not add reinforcement learning before logs, metrics, and replay.

## Module Responsibilities

### core

Shared primitives, configuration, logging, constants, errors, and common utilities.

### perception

Screen capture, frame preprocessing, computer vision, OCR, HUD recognition, minimap
recognition, and UI state classification.

### state

Canonical world state, temporal state history, confidence scoring, and state
transition detection.

### planning

Behavior trees, state machines, task planning, strategic LLM planning, JSON schema
validation, and fallback policies.

### execution

Action queue, bounded input actions, timeout, cancellation, safety checks, and
execution monitoring.

### evaluation

Metrics, replay, run reports, success/failure analysis, and performance reports.

## Current Phase

FASE 0 - Foundation.

No gameplay automation should be implemented in this phase.
