"""Tests for REST framework decorators, binding annotations, and ProblemDetails."""

from src.rest import (
    FromBody,
    FromHeader,
    FromPath,
    FromQuery,
    FromServices,
    ProblemDetails,
    RestValidationError,
    controller,
    delete,
    get,
    post,
    put,
)


def test_problem_details_rfc7807_serialization() -> None:
    problem = ProblemDetails(
        title="Validation Error",
        status=400,
        detail="One or more parameters were invalid.",
        errors={"name": ["Field 'name' is required."]},
    )
    data = problem.to_dict()

    assert data["title"] == "Validation Error"
    assert data["status"] == 400
    assert data["detail"] == "One or more parameters were invalid."
    assert data["errors"]["name"] == ["Field 'name' is required."]


def test_controller_and_route_decorators() -> None:
    @controller("/api/v1/users")
    class UserController:
        @get("")
        def list_users(self):
            pass

        @post("")
        def create_user(self):
            pass

        @get("/{id}")
        def get_user(self, id: str):
            pass

    assert getattr(UserController, "__is_controller__") is True
    assert getattr(UserController, "__controller_prefix__") == "/api/v1/users"

    inst = UserController()
    assert getattr(inst.list_users, "__route_method__") == "GET"
    assert getattr(inst.list_users, "__route_path__") == ""
    assert getattr(inst.create_user, "__route_method__") == "POST"
    assert getattr(inst.get_user, "__route_path__") == "/{id}"


def test_binding_annotations() -> None:
    q = FromQuery(name="q", default="sarathi")
    p = FromPath(name="id")
    b = FromBody(required=True)
    h = FromHeader(name="X-Custom")
    s = FromServices(service_type=object)

    assert q.name == "q"
    assert p.name == "id"
    assert b.required is True
    assert h.name == "X-Custom"
    assert s.service_type is object
