"""
PROJECT SARATHI

Bootstrap the Dependency Injection container.

Author:
    PROJECT SARATHI

Version:
    0.1.0
"""

from __future__ import annotations

from config.settings import settings
from src.lifecycle import LifecycleManager
from src.utils.logger import logger

from .container import ServiceContainer


def bootstrap_container() -> ServiceContainer:
    """
    Create and initialize the application's
    dependency injection container.

    Returns
    -------
    ServiceContainer
        Fully initialized service container.
    """

    container = ServiceContainer()

    # Register existing singleton instances.
    container.register_instance(
        "settings",
        settings,
    )

    container.register_instance(
        "logger",
        logger,
    )

    lifecycle = LifecycleManager(logger)

    container.register_instance(
        "lifecycle",
        lifecycle,
    )

    return container