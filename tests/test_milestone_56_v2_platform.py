"""Milestone 56 Tests."""
import asyncio
from sarathi.v2_platform import SarathiPlatform, PlatformConfig, SystemHealthProbe, PlatformMetricsReporter, PlatformBenchmarkSuite

def test_v2_platform_e2e():
    async def run():
        platform = SarathiPlatform(PlatformConfig(vector_dimension=32))
        await platform.boot()
        probe = SystemHealthProbe(platform)
        assert probe.check_readiness()

        res = await platform.execute_integrated_agentic_workflow("wf1", "doc1", "Sarathi v2.0.0 master release", "Sarathi v2.0.0")
        assert "node_outputs" in res

        benchmark = PlatformBenchmarkSuite(platform)
        b_res = await benchmark.run_stress_test(total_workflows=5, concurrency=2)
        assert b_res["status"] == "PASSED"

        await platform.shutdown()
    asyncio.run(run())
