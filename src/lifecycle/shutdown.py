"""
PROJECT SARATHI

Graceful shutdown handler.
"""


def graceful_shutdown(
    lifecycle_manager,
    logger
):

    logger.info(
        "Executing graceful shutdown"
    )


    lifecycle_manager.stop()


    logger.info(
        "Shutdown completed"
    )