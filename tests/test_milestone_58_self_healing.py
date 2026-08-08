"""
Unit and Integration Tests for Milestone 58: Autonomous AI Agent Self-Healing, Auto-Tuning & Dynamic Fallback Engine.
Tag: v2.2.0-ai-self-healing-engine
"""
import asyncio
import time
from sarathi.self_healing import CircuitState, AICircuitBreaker, ModelFallbackRouter, SelfHealingEngine

def test_circuit_breaker_states_and_tripping():
    async def run():
        cb = AICircuitBreaker(failure_threshold=2, recovery_timeout_sec=0.1)
        assert cb.state == CircuitState.CLOSED

        async def failing_fn(): raise RuntimeError("LLM API Error")

        # Call 1: fails
        try: await cb.call(failing_fn)
        except RuntimeError: pass
        assert cb.state == CircuitState.CLOSED

        # Call 2: fails -> trips breaker to OPEN
        try: await cb.call(failing_fn)
        except RuntimeError: pass
        assert cb.state == CircuitState.OPEN

        # Call 3: should be blocked while OPEN
        try:
            await cb.call(failing_fn)
            assert False, "Should block call when OPEN"
        except RuntimeError as e:
            assert "Circuit breaker is OPEN" in str(e)

        # Wait for recovery timeout
        await asyncio.sleep(0.12)

        async def success_fn(): return "recovered"

        # Half-open call succeeds -> resets to CLOSED
        res = await cb.call(success_fn)
        assert res == "recovered"
        assert cb.state == CircuitState.CLOSED

    asyncio.run(run())

def test_model_fallback_router():
    async def run():
        async def primary(p): raise TimeoutError("Primary LLM timeout")
        async def fallback1(p): raise RuntimeError("Fallback 1 error")
        async def fallback2(p): return f"Response to '{p}' from Fallback 2"

        router = ModelFallbackRouter(primary_driver=primary, fallback_drivers=[fallback1, fallback2])
        res = await router.execute_with_fallback("Hello AI")

        assert res["used_fallback"]
        assert res["driver_index"] == 2
        assert "Response to 'Hello AI'" in res["result"]

    asyncio.run(run())

def test_self_healing_engine_recovery():
    async def run():
        engine = SelfHealingEngine()

        async def broken_primary(): raise ValueError("Bad prompt format")
        async def healing_recovery(): return "Self-healed output format"

        res = await engine.execute_healable_task(
            task_id="task_llm_gen",
            primary_fn=broken_primary,
            recovery_fn=healing_recovery
        )

        assert res["status"] == "SUCCESS"
        assert res["healed"]
        assert res["result"] == "Self-healed output format"
        assert len(engine.healing_logs) >= 2

    asyncio.run(run())
