from src.container import (
    ServiceContainer,
    ServiceLifetime,
)


container = ServiceContainer()

container.register_instance(
    "number",
    42,
)

print(container.resolve("number"))

container.register_factory(
    "list",
    list,
    lifetime=ServiceLifetime.TRANSIENT,
)

a = container.resolve("list")

b = container.resolve("list")

print(a is b)

print("Container tests passed.")