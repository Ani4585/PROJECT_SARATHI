from src.container import ServiceRegistry

registry = ServiceRegistry()

registry.register(
    "number",
    lambda: 42,
)

print("Registered:", registry.list_services())

definition = registry.get_definition("number")

print("Lifetime:", definition.lifetime.value)

print("Registry test passed.")