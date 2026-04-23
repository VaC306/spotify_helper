class SpotifyCLIError(Exception):
    """Base exception for the application."""


class ConfigurationError(SpotifyCLIError):
    """Raised when required configuration is missing or invalid."""


class AuthenticationError(SpotifyCLIError):
    """Raised when Spotify authentication fails."""


class SpotifyAPIError(SpotifyCLIError):
    """Raised when the Spotify API returns an error."""


class StorageError(SpotifyCLIError):
    """Raised when local persistence fails."""


class PlaylistFileError(SpotifyCLIError):
    """Raised when a playlist TXT file cannot be processed."""
