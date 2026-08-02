"""Extension framework exceptions."""


class ExtensionError(Exception):
    """Base class for extension framework errors."""


class UnknownExtensionPointError(ExtensionError, KeyError):
    """Raised when an extension point has not been defined."""


class ExtensionConflictError(ExtensionError, ValueError):
    """Raised when registrations violate an extension-point policy."""


class ExtensionTypeError(ExtensionError, TypeError):
    """Raised when an extension does not implement the required contract."""
