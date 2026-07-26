from src.reflection import ConstructorInspector


class Example:

    def __init__(
        self,
        logger,
        settings,
        database,
    ):
        pass


deps = ConstructorInspector.get_dependencies(
    Example
)

print(deps)

print("Reflection tests passed.")