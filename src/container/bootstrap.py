"""
PROJECT SARATHI

Bootstrap the Dependency Injection container.

Author:
    PROJECT SARATHI

Version:
    0.1.0
"""

from __future__ import annotations

from logging import Logger

from config.settings import settings, Settings

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


    # -------------------------------------------------
    # Name-based registrations
    # Existing compatibility layer
    # -------------------------------------------------

    container.register_instance(
        "settings",
        settings,
    )

    container.register_instance(
        "logger",
        logger,
    )


    # -------------------------------------------------
    # Type-based registrations
    # New enterprise DI layer
    # -------------------------------------------------

    container.register_type(
        Settings,
        settings,
    )

    container.register_type(
        Logger,
        logger,
    )


    # -------------------------------------------------
    # Lifecycle service
    # -------------------------------------------------

    lifecycle = LifecycleManager(
        logger
    )


    container.register_instance(
        "lifecycle",
        lifecycle,
    )


    container.register_type(
        LifecycleManager,
        lifecycle,
    )


    return container