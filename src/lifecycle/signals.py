"""
PROJECT SARATHI

Operating System signal handling.
"""

import signal


def register_signal_handlers(lifecycle_manager, logger):
    """
    Register operating system signal handlers for graceful shutdown.
    """

    def signal_handler(signum, frame):
        logger.warning(
            "Shutdown signal received: %s",
            signal.Signals(signum).name,
        )

        lifecycle_manager.stop()

        logger.info(
            "Application terminated gracefully."
        )

        raise SystemExit(0)

    # Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    # SIGTERM (if supported on this platform)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, signal_handler)