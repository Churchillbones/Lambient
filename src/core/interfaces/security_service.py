"""Interface for security service operations.

Provides typed access to encryption, decryption, and secure data handling
operations throughout the application.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Tuple


class ISecurityService(ABC):
    """Interface for security and encryption operations."""

    @abstractmethod
    def get_encryption_key(self) -> bytes:
        """Return the application's encryption key, generating if needed."""

    @abstractmethod
    def encrypt_data(self, data: bytes) -> bytes:
        """Encrypt raw data using the application's encryption key."""

    @abstractmethod
    def decrypt_data(self, cipher: bytes) -> bytes:
        """Decrypt cipher data using the application's encryption key."""

    @abstractmethod
    def encrypt_audio_file(self, audio_path: Path) -> Tuple[Path, bool]:
        """Encrypt an audio file and return the encrypted path and success status."""

    @abstractmethod
    def decrypt_audio_file(self, encrypted_path: Path) -> Tuple[Path, bool]:
        """Decrypt an encrypted audio file and return the decrypted path and success status."""

    @abstractmethod
    def secure_audio_processing(self, audio_path: Path, use_encryption: bool) -> AbstractContextManager[Path]:
        """Context manager for secure audio processing with transparent encryption/decryption."""

    @abstractmethod
    def is_encrypted_file(self, file_path: Path) -> bool:
        """Check if a file is encrypted using our encryption format."""

    @abstractmethod
    def secure_delete(self, file_path: Path) -> bool:
        """Securely delete a file by overwriting its contents."""


__all__ = ["ISecurityService"] 