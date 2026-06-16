"""Command-line entry point for the Genshin AI research agent."""

import argparse
from pathlib import Path

from genshin_ai import __version__
from genshin_ai.core.config import load_config
from genshin_ai.core.logging import JsonlEventLogger, LogEvent, configure_console_logging
from genshin_ai.core.runtime import RuntimeContext


def main(argv: list[str] | None = None) -> None:
    """Run a minimal CLI sanity check.

    This command intentionally does not capture the screen, call models, or
    automate gameplay. It verifies package import, runtime context, typed
    configuration, and structured logging.
    """
    args = _parse_args(argv)
    config = load_config(args.config)
    config_source = str(args.config) if args.config is not None else "defaults"

    configure_console_logging()

    runtime = RuntimeContext()
    event_logger = JsonlEventLogger(runtime=runtime, log_dir=Path(config.logging.log_dir))

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
            },
        )
    )

    print(f"genshin-ai {__version__}")
    print(f"Run ID: {runtime.run_id}")
    print(f"Phase: {runtime.project_phase}")
    print(f"Config: {config_source}")
    print("Status: package import, runtime context, typed configuration, and logging OK")


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Genshin AI research agent CLI.")
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Optional TOML configuration file path.",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    main()
