"""
PROJECT SARATHI

Application health reporting.
"""


def get_health_status(
    settings,
    lifecycle_manager
):

    return {

        "application":
            settings.APP_NAME,

        "version":
            settings.VERSION,

        "environment":
            settings.ENVIRONMENT,

        "status":
            lifecycle_manager.get_state()
    }