"""
PROJECT SARATHI

Application

Central application object responsible for
startup, runtime coordination and shutdown.
"""

from __future__ import annotations

from .context import ApplicationContext


class Application:
    """
    Central application object.

    Responsibilities
    ----------------
    * Start the application
    * Coordinate lifecycle
    * Expose health information
    * Shut down gracefully
    """

    def __init__(
        self,
        context: ApplicationContext,
    ) -> None:

        self._context = context

    @property
    def context(self) -> ApplicationContext:
        """
        Return the application context.
        """

        return self._context

    def start(self) -> None:
        """
        Start the application.
        """

        lifecycle = self._context.lifecycle
        logger = self._context.logger

        lifecycle.start()
        lifecycle.mark_running()

        logger.info(
            "Application object started successfully."
        )

    def stop(self) -> None:
        """
        Stop the application.
        """

        logger = self._context.logger

        logger.info(
            "Stopping application..."
        )

        self._context.lifecycle.stop()

        logger.info(
            "Application stopped successfully."
        )

    def health(self) -> dict[str, str]:
        """
        Return application health information.
        """

        return {
            "application": self._context.settings.APP_NAME,
            "version": self._context.settings.VERSION,
            "environment": self._context.settings.ENVIRONMENT,
            "status": self._context.lifecycle.get_state(),
        }

    def run(self) -> None:
        """
        Run the application.
        """

        self.start()

        logger = self._context.logger

        logger.info(
            "Application is running."
        )

        logger.info(
            "Health: %s",
            self.health(),
        )

        self.stop()