"""
PROJECT SARATHI

Application Builder

Responsible for constructing a fully initialized
Application instance.
"""

from __future__ import annotations

from src.container import bootstrap_container

from .application import Application
from .context import ApplicationContext


class ApplicationBuilder:
    """
    Builds an Application instance.
    """

    def build(self) -> Application:
        """
        Build and return a fully configured application.
        """

        container = bootstrap_container()

        context = ApplicationContext(
            settings=container.resolve("settings"),
            logger=container.resolve("logger"),
            container=container,
            lifecycle=container.resolve("lifecycle"),
        )

        return Application(context)