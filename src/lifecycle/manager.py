"""
PROJECT SARATHI

Application Lifecycle Manager

Controls application startup,
runtime state and shutdown.
"""


from enum import Enum


class ApplicationState(Enum):
    """
    Possible application states.
    """

    STARTING = "STARTING"

    RUNNING = "RUNNING"

    STOPPING = "STOPPING"

    STOPPED = "STOPPED"

    FAILED = "FAILED"



class LifecycleManager:
    """
    Central lifecycle controller.
    """


    def __init__(self, logger):

        self.logger = logger

        self.state = ApplicationState.STOPPED



    def start(self):

        self.logger.info(
            "Application lifecycle starting"
        )

        self.state = ApplicationState.STARTING



    def mark_running(self):

        self.state = ApplicationState.RUNNING

        self.logger.info(
            "Application state: RUNNING"
        )



    def stop(self):

        self.state = ApplicationState.STOPPING

        self.logger.info(
            "Application shutdown initiated"
        )


        self.state = ApplicationState.STOPPED

        self.logger.info(
            "Application state: STOPPED"
        )



    def fail(self):

        self.state = ApplicationState.FAILED

        self.logger.error(
            "Application state: FAILED"
        )



    def get_state(self):

        return self.state.value