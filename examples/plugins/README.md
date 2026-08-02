# Integrated Plugin Example

Run the complete M24 example from the repository root:

```powershell
python .\examples\plugins\integrated_plugin.py
```

The example contributes a named service, developer command, lifecycle hook,
and typed extension. It starts the plugin, exercises every contribution, stops
the plugin, and confirms that unload removed every owned registration.
