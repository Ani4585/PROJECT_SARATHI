"""
PROJECT SARATHI
Global Exception Handling Framework
"""


import traceback


def handle_exception(
    exception,
    logger
):
    """
    Central production exception handler.
    """

    logger.exception(
        "Unhandled application exception",
        exc_info=True
    )


    return {
        "success": False,
        "error": str(exception),
        "type": exception.__class__.__name__,
    }



def install_global_exception_handler(logger):
    """
    Installs system-level exception capture.
    """


    def global_handler(
        exc_type,
        exc_value,
        exc_traceback
    ):

        if issubclass(
            exc_type,
            KeyboardInterrupt
        ):
            return


        logger.error(
            "Critical unhandled exception",
            exc_info=(
                exc_type,
                exc_value,
                exc_traceback
            )
        )


    import sys

    sys.excepthook = global_handler