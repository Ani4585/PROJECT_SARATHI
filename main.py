"""
PROJECT SARATHI

Application entry point.
"""

from config.settings import settings
from src.utils.logger import logger

from src.exceptions.handlers import (
    install_global_exception_handler
)


install_global_exception_handler(logger)


def main():

    logger.info("Starting PROJECT SARATHI")

    logger.info(
        "Application Name: %s",
        settings.APP_NAME
    )

    logger.info(
        "Version: %s",
        settings.VERSION
    )

    logger.info(
        "Environment: %s",
        settings.ENVIRONMENT
    )

    logger.info(
        "Project Root: %s",
        settings.PROJECT_ROOT
    )

    logger.warning(
        "This is a sample warning message."
    )

    logger.error(
        "This is a sample error message."
    )

    logger.info(
        "Application startup completed successfully."
    )


if __name__ == "__main__":
    main()