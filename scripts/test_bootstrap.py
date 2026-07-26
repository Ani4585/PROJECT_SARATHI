from src.container import bootstrap_container


container = bootstrap_container()

logger = container.resolve("logger")

settings = container.resolve("settings")

lifecycle = container.resolve("lifecycle")

print(type(logger).__name__)

print(type(settings).__name__)

print(type(lifecycle).__name__)

print(container.list_services())

print("Bootstrap test passed.")