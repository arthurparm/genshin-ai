"""Command-line entry point for the Genshin AI research agent."""

from pathlib import Path

from genshin_ai import __version__
from genshin_ai.core.logging import JsonlEventLogger, LogEvent, configure_console_logging
from genshin_ai.core.runtime import RuntimeContext


def main() -> None:
    """Run a minimal CLI sanity check.

    This command intentionally does not capture the screen, call models, or
    automate gameplay. It verifies package import, runtime context, and structured
    logging.
    """
    configure_console_logging()

    runtime = RuntimeContext()
    event_logger = JsonlEventLogger(runtime=runtime, log_dir=Path("logs"))

    event_logger.emit(
        LogEvent(
            event="cli_sanity_check",
            module="cli",
            message="CLI sanity check executed successfully.",
            data={
                "version": __version__,
                "phase": runtime.project_phase,
            },
        )
    )

    print(f"genshin-ai {__version__}")
    print(f"Run ID: {runtime.run_id}")
    print(f"Phase: {runtime.project_phase}")
    print("Status: package import, runtime context, and structured logging OK")


if __name__ == "__main__":
    main()
