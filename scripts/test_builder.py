from src.application import ApplicationBuilder

builder = ApplicationBuilder()

app = builder.build()

print(type(app).__name__)

print(app.health())

print("Builder test passed.")