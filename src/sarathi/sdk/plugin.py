from typing import Dict, Optional, Any

class BasePlugin:
    name: str = "base_plugin"
    version: str = "1.0.0"

    async def on_load(self, sdk: 'PluginSDK'):
        pass

    async def on_unload(self, sdk: 'PluginSDK'):
        pass

class PluginSDK:
    def __init__(self, framework_version: str = "1.0.0"):
        self.framework_version = framework_version
        self.plugins: Dict[str, BasePlugin] = {}
        self.extensions: Dict[str, Any] = {}

    async def register_plugin(self, plugin: BasePlugin):
        if plugin.name in self.plugins:
            raise ValueError(f"Plugin '{plugin.name}' is already registered")
        self.plugins[plugin.name] = plugin
        await plugin.on_load(self)

    async def unload_plugin(self, name: str):
        if name in self.plugins:
            plugin = self.plugins.pop(name)
            await plugin.on_unload(self)

    def register_extension(self, key: str, extension: Any):
        self.extensions[key] = extension

    def get_extension(self, key: str) -> Optional[Any]:
        return self.extensions.get(key)
