"""Application-specific exceptions."""


class MineBridgeError(Exception):
    """Base exception for MineBridge FRP."""


class ConfigurationError(MineBridgeError):
    """Raised when the current configuration is invalid."""


class ServiceError(MineBridgeError):
    """Raised when a managed service operation fails."""

