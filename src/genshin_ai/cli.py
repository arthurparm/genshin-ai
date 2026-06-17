"""Command-line entry point for the Genshin AI research agent."""

import argparse
from pathlib import Path

from genshin_ai import __version__
from genshin_ai.core.config import AppConfig, load_config
from genshin_ai.core.logging import JsonlEventLogger, JsonValue, LogEvent, configure_console_logging
from genshin_ai.core.runtime import RuntimeContext
from genshin_ai.core.session import RunSession, create_run_session
from genshin_ai.perception.benchmark import (
    run_capture_benchmark,
    save_capture_benchmark_report,
)
from genshin_ai.perception.capture import MockCaptureSource
from genshin_ai.perception.frame import CapturedFrame
from genshin_ai.perception.metrics import run_capture_smoke_test
from genshin_ai.perception.preprocess import (
    preprocess_frame,
    processed_frame_sample_path,
    save_processed_frame_sample_ppm,
)
from genshin_ai.perception.screen_capture import (
    MssScreenCaptureSource,
    ScreenCaptureDependencyError,
    sample_frame_path,
    save_frame_sample_ppm,
)


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

    if args.command == "screen-capture-smoke":
        _run_screen_capture_smoke_command(
            args,
            config,
            config_source,
            runtime,
            session,
            event_logger,
        )
        return

    if args.command == "capture-benchmark":
        _run_capture_benchmark_command(
            args,
            config,
            config_source,
            runtime,
            session,
            event_logger,
        )
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


def _run_screen_capture_smoke_command(
    args: argparse.Namespace,
    config: AppConfig,
    config_source: str,
    runtime: RuntimeContext,
    session: RunSession,
    event_logger: JsonlEventLogger,
) -> None:
    preprocess_backend = args.preprocess_backend or config.capture.preprocess_backend
    event_logger.emit(
        LogEvent(
            event="screen_capture_smoke_started",
            module="perception.screen_capture",
            data={
                "frames": args.frames,
                "preprocess": args.preprocess,
                "preprocess_backend": preprocess_backend if args.preprocess else None,
                "save_samples": args.save_samples,
                "config_source": config_source,
            },
        )
    )

    try:
        source = MssScreenCaptureSource()
    except ScreenCaptureDependencyError as error:
        event_logger.emit(
            LogEvent(
                event="screen_capture_dependency_missing",
                module="perception.screen_capture",
                level="ERROR",
                message=str(error),
            )
        )
        raise SystemExit(str(error)) from error

    saved_samples = 0

    def save_sample(frame: CapturedFrame) -> None:
        nonlocal saved_samples
        if args.preprocess:
            processed_frame = preprocess_frame(
                frame,
                target_width=config.capture.process_width,
                target_height=config.capture.process_height,
                backend=preprocess_backend,
            )
            event_logger.emit(
                LogEvent(
                    event="frame_preprocessed",
                    module="perception.preprocess",
                    data={
                        **dict[str, JsonValue](processed_frame.metadata()),
                        "preprocess_backend": preprocess_backend,
                    },
                )
            )
            output_path = save_processed_frame_sample_ppm(
                processed_frame,
                processed_frame_sample_path(session.captures_dir, processed_frame),
            )
            width = processed_frame.width
            height = processed_frame.height
        else:
            output_path = save_frame_sample_ppm(
                frame,
                sample_frame_path(session.captures_dir, frame),
            )
            width = frame.width
            height = frame.height

        saved_samples += 1
        event_logger.emit(
            LogEvent(
                event="screen_capture_sample_saved",
                module="perception.screen_capture",
                data={
                    "frame_id": frame.frame_id,
                    "path": str(output_path),
                    "width": width,
                    "height": height,
                    "preprocessed": args.preprocess,
                    "preprocess_backend": preprocess_backend if args.preprocess else None,
                },
            )
        )

    def preprocess_only(frame: CapturedFrame) -> None:
        processed_frame = preprocess_frame(
            frame,
            target_width=config.capture.process_width,
            target_height=config.capture.process_height,
            backend=preprocess_backend,
        )
        event_logger.emit(
            LogEvent(
                event="frame_preprocessed",
                module="perception.preprocess",
                data={
                    **dict[str, JsonValue](processed_frame.metadata()),
                    "preprocess_backend": preprocess_backend,
                },
            )
        )

    on_frame_captured = None
    if args.save_samples:
        on_frame_captured = save_sample
    elif args.preprocess:
        on_frame_captured = preprocess_only

    with source:
        metrics = run_capture_smoke_test(
            source=source,
            logger=event_logger,
            frame_count=args.frames,
            target_fps=config.capture.target_fps,
            on_frame_captured=on_frame_captured,
        )

    event_logger.emit(
        LogEvent(
            event="screen_capture_smoke_finished",
            module="perception.screen_capture",
            data={
                "frames": args.frames,
                "preprocess": args.preprocess,
                "preprocess_backend": preprocess_backend if args.preprocess else None,
                "saved_samples": saved_samples,
                "metrics": metrics.to_dict(),
            },
        )
    )

    print(f"genshin-ai {__version__}")
    print(f"Run ID: {runtime.run_id}")
    print(f"Phase: {runtime.project_phase}")
    print(f"Config: {config_source}")
    print(f"Run session: {session.root_dir}")
    print(f"Capture source: {source.source}")
    print(f"Frames captured: {metrics.frames_captured}")
    print(f"Target FPS: {metrics.target_fps}")
    print(f"Actual FPS: {metrics.actual_fps:.2f}")
    print(f"Failed frames: {metrics.failed_frames}")
    print(f"Preprocess: {args.preprocess}")
    if args.preprocess:
        print(f"Preprocess backend: {preprocess_backend}")
    print(f"Samples saved: {saved_samples}")


def _run_capture_benchmark_command(
    args: argparse.Namespace,
    config: AppConfig,
    config_source: str,
    runtime: RuntimeContext,
    session: RunSession,
    event_logger: JsonlEventLogger,
) -> None:
    preprocess_backend = args.preprocess_backend or config.capture.preprocess_backend
    try:
        source = MssScreenCaptureSource()
    except ScreenCaptureDependencyError as error:
        event_logger.emit(
            LogEvent(
                event="screen_capture_dependency_missing",
                module="perception.screen_capture",
                level="ERROR",
                message=str(error),
            )
        )
        raise SystemExit(str(error)) from error

    with source:
        report = run_capture_benchmark(
            source=source,
            runtime=runtime,
            session=session,
            logger=event_logger,
            frames=args.frames,
            preprocess=args.preprocess,
            preprocess_backend=preprocess_backend,
            process_width=config.capture.process_width,
            process_height=config.capture.process_height,
            save_every=args.save_every,
        )
    report_path = save_capture_benchmark_report(
        report,
        session.artifacts_dir / "capture_benchmark.json",
    )

    print(f"genshin-ai {__version__}")
    print(f"Run ID: {runtime.run_id}")
    print(f"Phase: {runtime.project_phase}")
    print(f"Config: {config_source}")
    print(f"Run session: {session.root_dir}")
    print(f"Capture source: {source.source}")
    print(f"Frames requested: {report.frames_requested}")
    print(f"Frames captured: {report.frames_captured}")
    print(f"Failed frames: {report.failed_frames}")
    print(f"Preprocess: {report.preprocess_enabled}")
    print(f"Preprocess backend: {report.preprocess_backend}")
    print(f"Actual FPS: {report.actual_fps:.2f}")
    print(f"Average capture ms: {report.average_capture_ms:.2f}")
    print(f"Average preprocess ms: {report.average_preprocess_ms:.2f}")
    print(f"Average total frame ms: {report.average_total_frame_ms:.2f}")
    print(f"Samples saved: {report.samples_saved}")
    print(f"Report: {report_path}")


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
    screen_capture_smoke_parser = subparsers.add_parser(
        "screen-capture-smoke",
        help="Run a bounded real screen-capture smoke test.",
    )
    screen_capture_smoke_parser.add_argument(
        "--frames",
        type=int,
        default=5,
        help="Number of frames to capture.",
    )
    screen_capture_smoke_parser.add_argument(
        "--save-samples",
        action="store_true",
        help="Save captured sample frames as PPM files.",
    )
    screen_capture_smoke_parser.add_argument(
        "--preprocess",
        action="store_true",
        help="Preprocess captured frames to configured RGB resolution.",
    )
    screen_capture_smoke_parser.add_argument(
        "--preprocess-backend",
        choices=("python", "pillow"),
        default=None,
        help="Preprocessing backend to use when --preprocess is enabled.",
    )
    screen_capture_smoke_parser.add_argument(
        "--config",
        type=Path,
        default=argparse.SUPPRESS,
        help="Optional TOML configuration file path.",
    )
    capture_benchmark_parser = subparsers.add_parser(
        "capture-benchmark",
        help="Run an operational screen-capture benchmark.",
    )
    capture_benchmark_parser.add_argument(
        "--frames",
        type=int,
        default=60,
        help="Number of frames to benchmark.",
    )
    capture_benchmark_parser.add_argument(
        "--preprocess",
        action="store_true",
        help="Benchmark preprocessing to configured RGB resolution.",
    )
    capture_benchmark_parser.add_argument(
        "--preprocess-backend",
        choices=("python", "pillow"),
        default=None,
        help="Preprocessing backend to use when --preprocess is enabled.",
    )
    capture_benchmark_parser.add_argument(
        "--save-every",
        type=int,
        default=None,
        help="Save one sample every N attempted frames.",
    )
    capture_benchmark_parser.add_argument(
        "--config",
        type=Path,
        default=argparse.SUPPRESS,
        help="Optional TOML configuration file path.",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    main()
