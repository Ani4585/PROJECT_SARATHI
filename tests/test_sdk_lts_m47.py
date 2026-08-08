import asyncio
import warnings
import pytest
from sarathi.sdk import deprecated, FrameworkDeprecationWarning, BasePlugin, PluginSDK
from sarathi.lts import LTSMaintenancePolicy, LTSHealthChecker

def test_deprecated_warning_emission():
    @deprecated(reason="Legacy helper", replacement="new_helper", retired_in_version="1.2.0")
    def legacy_fn():
        return "legacy_data"

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        res = legacy_fn()
        assert res == "legacy_data"
        assert len(w) == 1
        assert issubclass(w[0].category, FrameworkDeprecationWarning)
        assert "Use 'new_helper' instead" in str(w[0].message)

def test_plugin_sdk_lifecycle():
    async def _test():
        sdk = PluginSDK(framework_version="1.0.0")

        class AnalyticsPlugin(BasePlugin):
            name = "analytics"
            version = "1.0.0"

            async def on_load(self, sdk):
                sdk.register_extension("tracker", "TrackerInstance")

            async def on_unload(self, sdk):
                sdk.extensions.pop("tracker", None)

        plugin = AnalyticsPlugin()
        await sdk.register_plugin(plugin)
        assert sdk.get_extension("tracker") == "TrackerInstance"

        await sdk.unload_plugin("analytics")
        assert sdk.get_extension("tracker") is None
        assert "analytics" not in sdk.plugins

    asyncio.run(_test())

def test_lts_health_checker():
    checker = LTSHealthChecker()
    status = checker.check_lts_status()
    assert status["status"] == "HEALTHY"
    assert status["is_lts"] is True
    assert status["version"] == "1.0.0"
