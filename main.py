"""
PROJECT SARATHI

Application entry point.
"""

from config.settings import settings
from src.utils.logger import logger

from src.exceptions.handlers import (
    install_global_exception_handler
)
from src.lifecycle import (
    LifecycleManager,
    validate_environment,
    graceful_shutdown,
    get_health_status,
    register_signal_handlers,
)

install_global_exception_handler(logger)
lifecycle = LifecycleManager(logger)
register_signal_handlers(
    lifecycle,
    logger
)

def main():

    lifecycle.start()

    try:

        if not validate_environment(
            settings,
            logger
        ):

            lifecycle.fail()
            return


        logger.info(
            "Starting PROJECT SARATHI"
        )


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


        lifecycle.mark_running()


        health = get_health_status(
            settings,
            lifecycle
        )


        logger.info(
            "Application Health: %s",
            health
        )


        logger.info(
            "Application startup completed successfully."
        )


    except Exception as error:

        lifecycle.fail()

        logger.exception(
            "Application execution failed",
            exc_info=error
        )


    finally:

        graceful_shutdown(
            lifecycle,
            logger
        )
if __name__ == "__main__":
    main()