from src.container import bootstrap_container


class ExampleService:

    def __init__(
        self,
        logger,
        settings,
    ):
        self.logger = logger
        self.settings = settings


container = bootstrap_container()

service = container.build(
    ExampleService
)

print(type(service).__name__)
print(service.logger.__class__.__name__)
print(service.settings.__class__.__name__)

print("Constructor injection passed.")