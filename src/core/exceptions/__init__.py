"""Core exception hierarchy for the ambient transcription application.

This module provides domain-specific exceptions that replace generic exceptions
throughout the application, enabling better error handling and debugging.
"""

from __future__ import annotations


class AmbientScribeError(Exception):
    """Base exception for all ambient scribe application errors."""
    pass


class ConfigurationError(AmbientScribeError):
    """Raised when there are configuration-related issues."""
    pass


class ServiceNotFoundError(AmbientScribeError):
    """Raised when a requested service cannot be found in the DI container."""
    pass


class TranscriptionError(AmbientScribeError):
    """Base exception for transcription-related errors."""
    pass


class TranscriberNotFoundError(TranscriptionError):
    """Raised when a requested transcriber type is not available."""
    pass


class AudioProcessingError(TranscriptionError):
    """Raised when audio processing operations fail."""
    pass


class ModelLoadError(TranscriptionError):
    """Raised when a transcription model fails to load."""
    pass


class LLMError(AmbientScribeError):
    """Base exception for LLM-related errors."""
    pass


class LLMProviderError(LLMError):
    """Raised when an LLM provider encounters an error."""
    pass


class LLMConnectionError(LLMError):
    """Raised when connection to LLM service fails."""
    pass


class SecurityError(AmbientScribeError):
    """Base exception for security-related errors."""
    pass


class EncryptionError(SecurityError):
    """Raised when encryption/decryption operations fail."""
    pass


class AuthenticationError(SecurityError):
    """Raised when authentication fails."""
    pass


__all__ = [
    "AmbientScribeError",
    "ConfigurationError", 
    "ServiceNotFoundError",
    "TranscriptionError",
    "TranscriberNotFoundError",
    "AudioProcessingError",
    "ModelLoadError",
    "LLMError",
    "LLMProviderError", 
    "LLMConnectionError",
    "SecurityError",
    "EncryptionError",
    "AuthenticationError",
] 