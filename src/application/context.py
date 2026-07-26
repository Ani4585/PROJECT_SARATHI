"""
PROJECT SARATHI

Application Context

Stores shared application services that are
available throughout the lifetime of the application.
"""

from __future__ import annotations

from dataclasses import dataclass

from config.settings import Settings
from src.container import ServiceContainer
from src.lifecycle import LifecycleManager


@dataclass(slots=True)
class ApplicationContext:
    """
    Shared runtime context for the application.

    Attributes
    ----------
    settings
        Application configuration.

    logger
        Central application logger.

    container
        Dependency injection container.

    lifecycle
        Application lifecycle manager.
    """

    settings: Settings
    logger: object
    container: ServiceContainer
    lifecycle: LifecycleManager