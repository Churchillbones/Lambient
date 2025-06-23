from __future__ import annotations

"""Concrete factory for application configuration.

This factory ensures that *ApplicationSettings* is instantiated once and that
a corresponding *ConfigurationService* singleton is registered with the global
service container. Subsequent calls return the already-created instances.
"""

from threading import Lock
from typing import Optional

from ..config.settings import ApplicationSettings
from ..config.configuration_service import ConfigurationService
from ..container import global_container
from ..interfaces.config_service import IConfigurationService
from ..interfaces.config_factory import IConfigFactory

__all__ = [
    "ConfigFactory",
]


class ConfigFactory(IConfigFactory):
    """Singleton-style configuration factory."""

    _lock: Lock = Lock()
    _settings: Optional[ApplicationSettings] = None
    _service: Optional[ConfigurationService] = None

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def settings(self) -> ApplicationSettings:  # noqa: D401
        """Return lazily-created :class:`ApplicationSettings`."""
        if self._settings is None:
            with self._lock:
                if self._settings is None:  # double-checked
                    self._settings = ApplicationSettings()
        return self._settings

    def service(self) -> IConfigurationService:  # noqa: D401
        """Return lazily-created :class:`ConfigurationService`."""
        if self._service is None:
            with self._lock:
                if self._service is None:
                    self._service = ConfigurationService(settings=self.settings())
                    # Register singleton if not already present.
                    if IConfigurationService not in global_container.registrations:
                        global_container.register_instance(IConfigurationService, self._service)
        return self._service 