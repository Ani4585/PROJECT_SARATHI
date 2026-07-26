"""
PROJECT SARATHI

Lifecycle Manager Test
"""

from src.lifecycle import LifecycleManager
from src.utils.logger import logger


def main():
    lifecycle = LifecycleManager(logger)

    assert lifecycle.get_state() == "STOPPED"

    lifecycle.start()
    assert lifecycle.get_state() == "STARTING"

    lifecycle.mark_running()
    assert lifecycle.get_state() == "RUNNING"

    lifecycle.stop()
    assert lifecycle.get_state() == "STOPPED"

    print("Lifecycle tests passed successfully.")


if __name__ == "__main__":
    main()