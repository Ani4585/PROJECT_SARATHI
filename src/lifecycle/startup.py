"""
PROJECT SARATHI

Startup validation checks.
"""


from pathlib import Path



def validate_environment(settings, logger):

    """
    Validate required runtime environment.
    """


    logger.info(
        "Running startup validation"
    )


    checks = []


    project_root = Path(
        settings.PROJECT_ROOT
    )


    checks.append(
        project_root.exists()
    )


    if all(checks):

        logger.info(
            "Startup validation successful"
        )

        return True



    logger.error(
        "Startup validation failed"
    )

    return False