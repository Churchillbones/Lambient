from __future__ import annotations

"""Application bootstrap helper for Phase-1 infrastructure.

Importing this module wires up:
• ConfigurationService (already registered via core.config)  
• TranscriberFactory  
• LLMProviderFactory

After import you can fetch the container via :pydata:`container` and resolve
any registered singletons:

>>> from core.bootstrap import container
>>> cfg = container.resolve(IConfigurationService)
"""

from .container import global_container as container
from .factories.transcriber_factory import TranscriberFactory
from .factories.llm_factory import LLMProviderFactory
from .services.token_service import OpenAITokenService  # noqa: F401 – import side-effect
from .factories.config_factory import ConfigFactory
from .services.audio_service import AudioService
from .services.streaming_service import StreamingService

# Register singleton factory instances if not already present.
if TranscriberFactory not in container.registrations:
    container.register_instance(TranscriberFactory, TranscriberFactory())

if LLMProviderFactory not in container.registrations:
    container.register_instance(LLMProviderFactory, LLMProviderFactory())

if ConfigFactory not in container.registrations:
    container.register_instance(ConfigFactory, ConfigFactory())

# Phase-5: register centralised AudioService singleton
from .interfaces.audio_service import IAudioService  # noqa: E402

if IAudioService not in container.registrations:
    container.register_instance(IAudioService, AudioService())

# Streaming service singleton
from .interfaces.streaming_service import IStreamingService  # noqa: E402

if IStreamingService not in container.registrations:
    container.register_instance(IStreamingService, StreamingService()) 