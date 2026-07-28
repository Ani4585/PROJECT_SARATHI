from src.container.dependency_tree_builder import (
    DependencyTreeBuilder,
)
from src.graph import DependencyGraph
from src.reflection import ConstructorInspector


class Database:
    pass


class Repository:
    def __init__(
        self,
        database: Database,
    ) -> None:
        self.database = database


class Application:
    def __init__(
        self,
        repository: Repository,
    ) -> None:
        self.repository = repository


def test_recursive_dependency_tree_builder():

    graph = DependencyGraph()

    builder = DependencyTreeBuilder(
        graph,
        ConstructorInspector(),
    )

    builder.build(
        Application
    )

    application = graph.get_node(
        Application
    )

    repository = graph.get_node(
        Repository
    )

    database = graph.get_node(
        Database
    )

    assert application is not None
    assert repository is not None
    assert database is not None

    assert repository in application.dependencies
    assert database in repository.dependencies
    assert len(graph) == 3
    