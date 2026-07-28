from src.container.validator import DependencyValidator
from src.graph import DependencyGraph


def test_validator():

    graph = DependencyGraph()

    validator = DependencyValidator(
        graph
    )

    validator.validate()