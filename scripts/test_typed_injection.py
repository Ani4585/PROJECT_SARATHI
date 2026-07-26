from logging import Logger

from config.settings import Settings

from src.container import bootstrap_container


class TypedService:

    def __init__(
        self,
        logger: Logger,
        settings: Settings,
    ):

        self.logger = logger
        self.settings = settings



container = bootstrap_container()


service = container.build(
    TypedService
)


print(
    type(service).__name__
)

print(
    type(service.settings).__name__
)

print(
    type(service.logger).__name__
)


print(
    "Typed injection passed."
)