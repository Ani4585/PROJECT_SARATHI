from src.application.application import Application
from src.application.context import ApplicationContext
from src.container import bootstrap_container

container = bootstrap_container()

context = ApplicationContext(
    settings=container.resolve("settings"),
    logger=container.resolve("logger"),
    container=container,
    lifecycle=container.resolve("lifecycle"),
)

app = Application(context)

print(app.health())

print("Application test passed.")