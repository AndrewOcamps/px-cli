class PxError(Exception):
    """Base exception for all Proxmox CLI errors."""


class ConfigError(PxError):
    """Configuration is missing or invalid."""


class AuthError(PxError):
    """Authentication failed."""


class ApiError(PxError):
    """Proxmox API returned an error."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(f"API error {status_code}: {message}")


class NotFoundError(ApiError):
    """Requested resource was not found."""

    def __init__(self, resource: str = "") -> None:
        self.resource = resource
        msg = f"Resource not found: {resource}" if resource else "Resource not found"
        super().__init__(404, msg)
