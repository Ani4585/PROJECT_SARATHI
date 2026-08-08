import functools
import inspect
import warnings
from typing import Optional, Any

class FrameworkDeprecationWarning(Warning):
    """Custom deprecation warning for Project Sarathi framework features."""
    pass

def deprecated(reason: str, replacement: Optional[str] = None, retired_in_version: str = "2.0.0"):
    def decorator(fn_or_cls: Any):
        msg = f"'{fn_or_cls.__name__}' is deprecated: {reason}."
        if replacement:
            msg += f" Use '{replacement}' instead."
        msg += f" Scheduled for removal in v{retired_in_version}."

        if inspect.isclass(fn_or_cls):
            orig_init = fn_or_cls.__init__
            @functools.wraps(orig_init)
            def new_init(self, *args, **kwargs):
                warnings.warn(msg, category=FrameworkDeprecationWarning, stacklevel=2)
                orig_init(self, *args, **kwargs)
            fn_or_cls.__init__ = new_init
            return fn_or_cls
        elif inspect.iscoroutinefunction(fn_or_cls):
            @functools.wraps(fn_or_cls)
            async def wrapper(*args, **kwargs):
                warnings.warn(msg, category=FrameworkDeprecationWarning, stacklevel=2)
                return await fn_or_cls(*args, **kwargs)
            return wrapper
        else:
            @functools.wraps(fn_or_cls)
            def wrapper(*args, **kwargs):
                warnings.warn(msg, category=FrameworkDeprecationWarning, stacklevel=2)
                return fn_or_cls(*args, **kwargs)
            return wrapper
    return decorator
