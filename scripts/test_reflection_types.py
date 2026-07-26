from logging import Logger

from config.settings import Settings

from src.reflection import ConstructorInspector


class Example:

    def __init__(
        self,
        logger: Logger,
        settings: Settings,
    ):
        pass


types = ConstructorInspector.get_dependency_types(
    Example
)

print(
    [t.__name__ for t in types]
)

print("Reflection type inspection passed.")