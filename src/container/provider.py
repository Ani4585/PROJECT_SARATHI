"""
PROJECT SARATHI

Provider helper utilities.
"""


class FactoryProvider:
    """
    Wraps a callable used to create service instances.
    """

    def __init__(self, factory):
        self._factory = factory

    def create(self):
        return self._factory()