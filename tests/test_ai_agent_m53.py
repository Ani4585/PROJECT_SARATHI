import asyncio
import sarathi
import pytest
from sarathi.ai import tool, AIAgent, ToolSpec

def test_ai_version():
    assert sarathi.__version__ == "1.7.0"

def test_tool_decorator_schema_generation():
    @tool(name="get_user", description="Fetch user records")
    def get_user(user_id: int, include_metadata: bool = False):
        return f"user_{user_id}"

    spec = getattr(get_user, "_tool_spec")
    assert spec.name == "get_user"
    assert spec.parameters["properties"]["user_id"]["type"] == "integer"
    assert spec.parameters["properties"]["include_metadata"]["type"] == "boolean"

def test_ai_agent_tool_binding_and_execution():
    async def _test():
        agent = AIAgent(agent_name="TestAgent")

        @tool(name="calc_add")
        async def add(a: int, b: int) -> int:
            return a + b

        agent.bind_tool(add)
        res = await agent.execute_tool_call("calc_add", {"a": 15, "b": 25})
        assert res == 40

    asyncio.run(_test())
