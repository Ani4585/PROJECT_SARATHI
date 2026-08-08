import asyncio
import sarathi
import pytest
from sarathi.platform import SarathiPlatform, PlatformConfig, PlatformHealthReport

def test_platform_version():
    assert sarathi.__version__ >= "1.5.0"

def test_platform_orchestrator_lifecycle_and_health():
    async def _test():
        platform = SarathiPlatform()
        report_before = platform.get_health_report()
        assert report_before.is_healthy is False

        await platform.start()
        assert platform.is_started is True
        report_after = platform.get_health_report()
        assert report_after.is_healthy is True
        assert len(report_after.subsystems) == 13

        await platform.stop()
        assert platform.is_stopped is True

    asyncio.run(_test())
