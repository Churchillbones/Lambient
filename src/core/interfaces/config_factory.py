from __future__ import annotations

"""Interface for configuration factory.

Provides typed access to the application settings object as well as the
configuration service wrapper. Implementations should cache the settings to
avoid expensive re-validation on every call.
"""

from abc import ABC, abstractmethod
from typing import Protocol

from ..config.settings import ApplicationSettings  # noqa: E402 – avoid circular
from ..interfaces.config_service import IConfigurationService  # noqa: E402 – avoid circular

__all__ = [
    "IConfigFactory",
]


class IConfigFactory(Protocol):
    """Factory that exposes configuration singletons."""

    @abstractmethod
    def settings(self) -> ApplicationSettings:  # noqa: D401
        """Return the cached :class:`ApplicationSettings` instance."""

    @abstractmethod
    def service(self) -> IConfigurationService:  # noqa: D401
        """Return the cached :class:`IConfigurationService` implementation.""" 