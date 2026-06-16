"""Command-line entry point for the Genshin AI research agent."""

import argparse
from pathlib import Path

from genshin_ai import __version__
from genshin_ai.core.config import AppConfig, load_config
from genshin_ai.core.logging import JsonlEventLogger, LogEvent, configure_console_logging
from genshin_ai.core.runtime import RuntimeContext
from genshin_ai.core.session import RunSession, create_run_session
from genshin_ai.perception.capture import MockCaptureSource
from genshin_ai.perception.metrics import run_capture_smoke_test


def main(argv: list[str] | None = None) -> None:
    """Run the command-line interface.

    This command intentionally does not capture the screen, call models, or
    automate gameplay. The capture smoke command uses a mock source only.
    """
    args = _parse_args(argv)
    config = load_config(args.config)
    config_source = str(args.config) if args.config is not None else "defaults"

    configure_console_logging()

    runtime = RuntimeContext()
    session = create_run_session(runtime=runtime, config=config)
    event_logger = JsonlEventLogger(
        runtime=runtime,
        log_dir=session.logs_dir,
        filename="events.jsonl",
    )

    if args.command == "capture-smoke":
        _run_capture_smoke_command(config, config_source, runtime, session, event_logger)
        return

    _run_sanity_check(config, config_source, runtime, session, event_logger)


def _run_sanity_check(
    config: AppConfig,
    config_source: str,
    runtime: RuntimeContext,
    session: RunSession,
    event_logger: JsonlEventLogger,
) -> None:
    event_logger.emit(
        LogEvent(
            event="cli_sanity_check",
            module="cli",
            message="CLI sanity check executed successfully.",
            data={
                "version": __version__,
                "phase": runtime.project_phase,
                "config_source": config_source,
                "config": config.to_dict(),
                "session": session.to_dict(),
            },
        )
    )

    print(f"genshin-ai {__version__}")
    print(f"Run ID: {runtime.run_id}")
    print(f"Phase: {runtime.project_phase}")
    print(f"Config: {config_source}")
    print(f"Run session: {session.root_dir}")
    print("Status: package import, runtime context, typed configuration, and logging OK")


def _run_capture_smoke_command(
    config: AppConfig,
    config_source: str,
    runtime: RuntimeContext,
    session: RunSession,
    event_logger: JsonlEventLogger,
) -> None:
    source = MockCaptureSource(
        width=config.capture.process_width,
        height=config.capture.process_height,
    )
    metrics = run_capture_smoke_test(
        source=source,
        logger=event_logger,
        frame_count=5,
        target_fps=config.capture.target_fps,
    )

    print(f"genshin-ai {__version__}")
    print(f"Run ID: {runtime.run_id}")
    print(f"Phase: {runtime.project_phase}")
    print(f"Config: {config_source}")
    print(f"Run session: {session.root_dir}")
    print(f"Capture source: {source.source}")
    print(f"Frame size: {config.capture.process_width}x{config.capture.process_height}")
    print(f"Frames captured: {metrics.frames_captured}")
    print(f"Target FPS: {metrics.target_fps}")
    print(f"Actual FPS: {metrics.actual_fps:.2f}")
    print(f"Failed frames: {metrics.failed_frames}")


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Genshin AI research agent CLI.")
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Optional TOML configuration file path.",
    )
    subparsers = parser.add_subparsers(dest="command")
    capture_smoke_parser = subparsers.add_parser(
        "capture-smoke",
        help="Run a bounded mock capture smoke test without screen capture.",
    )
    capture_smoke_parser.add_argument(
        "--config",
        type=Path,
        default=argparse.SUPPRESS,
        help="Optional TOML configuration file path.",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    main()
