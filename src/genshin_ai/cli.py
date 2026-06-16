"""Command-line entry point for the Genshin AI research agent."""

from genshin_ai import __version__


def main() -> None:
    """Run a minimal CLI sanity check.

    This command intentionally does not capture the screen, call models, or automate
    gameplay. It exists only to verify that the package is installed and importable
    during FASE 0.
    """
    print(f"genshin-ai {__version__}")
    print("Phase: FASE 0 - Foundation")
    print("Status: package import and CLI sanity check OK")


if __name__ == "__main__":
    main()
