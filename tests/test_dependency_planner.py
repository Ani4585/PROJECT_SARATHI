from src.container.dependency_plan import DependencyPlan


def test_dependency_plan_creation():

    class Service:
        pass

    plan = DependencyPlan(Service)

    assert plan.service_type is Service

    assert plan.children == []

    assert plan.dependency_count == 0