"""Concrete implementation of security service.

Consolidates all encryption and security operations from the legacy modules
into a single, testable service that can be injected via DI container.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
import wave
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from typing import Iterator, Tuple

from cryptography.fernet import Fernet

from ..container import global_container
from ..exceptions import EncryptionError, ConfigurationError
from ..interfaces.config_service import IConfigurationService
from ..interfaces.security_service import ISecurityService

logger = logging.getLogger("ambient_scribe")


class SecurityService(ISecurityService):
    """Concrete implementation of security service."""

    def __init__(self) -> None:
        self._key_cache: bytes | None = None

    def _get_config_dirs(self) -> dict[str, Path]:
        """Return directories for key storage and temp cache."""
        try:
            cfg = global_container.resolve(IConfigurationService)
            base_dir: Path = cfg.get("base_dir", Path("./app_data"))  # type: ignore[arg-type]
        except Exception:  # pragma: no cover – DI not ready
            base_dir = Path("./app_data")
        return {
            "key_dir": base_dir / "keys",
            "cache_dir": base_dir / "cache",
        }

    def get_encryption_key(self) -> bytes:
        """Return a Fernet key; generate one if not present on disk."""
        if self._key_cache is not None:
            return self._key_cache

        conf = self._get_config_dirs()
        conf["key_dir"].mkdir(parents=True, exist_ok=True)
        key_file = conf["key_dir"] / "encryption_key.bin"
        
        if not key_file.exists():
            key = Fernet.generate_key()
            try:
                key_file.write_bytes(key)
                logger.info("Generated new encryption key at %s", key_file)
            except Exception as exc:
                raise EncryptionError(f"Failed to save encryption key: {exc}") from exc
        else:
            try:
                key = key_file.read_bytes()
                if len(key) != 44:  # Fernet key is 32 bytes base64 => 44 ascii chars
                    raise EncryptionError(f"Invalid encryption key length: {len(key)}")
            except Exception as exc:
                raise EncryptionError(f"Failed to read encryption key: {exc}") from exc

        self._key_cache = key
        return key

    def encrypt_data(self, data: bytes) -> bytes:
        """Encrypt raw data using the application's encryption key."""
        try:
            key = self.get_encryption_key()
            return Fernet(key).encrypt(data)
        except Exception as exc:
            logger.error("Data encryption failed: %s", exc)
            raise EncryptionError(f"Encryption failed: {exc}") from exc

    def decrypt_data(self, cipher: bytes) -> bytes:
        """Decrypt cipher data using the application's encryption key."""
        try:
            key = self.get_encryption_key()
            return Fernet(key).decrypt(cipher)
        except Exception as exc:
            logger.error("Data decryption failed: %s", exc)
            raise EncryptionError(f"Decryption failed: {exc}") from exc

    def encrypt_audio_file(self, audio_path: Path) -> Tuple[Path, bool]:
        """Encrypt an audio file and return the encrypted path and success status."""
        try:
            with wave.open(str(audio_path), "rb") as wf:
                meta = {
                    "channels": wf.getnchannels(),
                    "sampwidth": wf.getsampwidth(),
                    "framerate": wf.getframerate(),
                    "nframes": wf.getnframes(),
                }
                frames = wf.readframes(meta["nframes"])
        except wave.Error as exc:
            logger.error("Error reading WAV file %s: %s", audio_path, exc)
            return audio_path, False

        try:
            cipher = self.encrypt_data(frames)
            meta["encrypted"] = True
            meta_json = json.dumps(meta).encode()

            enc_path = audio_path.with_suffix(".enc")
            with open(enc_path, "wb") as fh:
                fh.write(b"MENC")  # magic
                fh.write((1).to_bytes(4, "little"))  # version
                fh.write(len(meta_json).to_bytes(4, "little"))
                fh.write(meta_json)
                fh.write(cipher)

            logger.info("Encrypted audio saved to %s", enc_path)
            return enc_path, True
        except Exception as exc:
            logger.error("Audio encryption failed: %s", exc)
            return audio_path, False

    def decrypt_audio_file(self, encrypted_path: Path) -> Tuple[Path, bool]:
        """Decrypt an encrypted audio file and return the decrypted path and success status."""
        try:
            with open(encrypted_path, "rb") as fh:
                if fh.read(4) != b"MENC":
                    raise EncryptionError("Invalid encrypted audio file")
                version = int.from_bytes(fh.read(4), "little")
                if version != 1:
                    raise EncryptionError(f"Unsupported encryption version: {version}")
                meta_len = int.from_bytes(fh.read(4), "little")
                meta = json.loads(fh.read(meta_len))
                cipher = fh.read()

            frames = self.decrypt_data(cipher)
            conf = self._get_config_dirs()
            conf["cache_dir"].mkdir(parents=True, exist_ok=True)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav", dir=conf["cache_dir"]) as tmp:
                wav_tmp = Path(tmp.name)

            with wave.open(str(wav_tmp), "wb") as wf:
                wf.setnchannels(meta["channels"])
                wf.setsampwidth(meta["sampwidth"])
                wf.setframerate(meta["framerate"])
                wf.writeframes(frames)

            return wav_tmp, True
        except Exception as exc:
            logger.error("Audio decryption failed: %s", exc)
            return encrypted_path, False

    @contextmanager
    def secure_audio_processing(self, audio_path: Path, use_encryption: bool) -> Iterator[Path]:
        """Context manager for secure audio processing with transparent encryption/decryption."""
        if not use_encryption:
            yield audio_path
            return

        enc_path, ok = self.encrypt_audio_file(audio_path)
        if not ok:
            logger.warning("Encryption failed; processing unencrypted audio")
            yield audio_path
            return

        dec_path, ok = self.decrypt_audio_file(enc_path)
        if not ok:
            logger.warning("Decryption failed; processing unencrypted audio")
            yield audio_path
            return

        try:
            yield dec_path
        finally:
            dec_path.unlink(missing_ok=True)

    def is_encrypted_file(self, file_path: Path) -> bool:
        """Check if a file is encrypted using our encryption format."""
        try:
            with open(file_path, "rb") as fh:
                return fh.read(4) == b"MENC"
        except Exception:
            return False

    def secure_delete(self, file_path: Path) -> bool:
        """Securely delete a file by overwriting its contents."""
        try:
            if not file_path.exists():
                return True
                
            # Overwrite with random data multiple times
            file_size = file_path.stat().st_size
            with open(file_path, "r+b") as f:
                for _ in range(3):  # 3 passes
                    f.seek(0)
                    f.write(os.urandom(file_size))
                    f.flush()
                    os.fsync(f.fileno())
            
            # Finally delete the file
            file_path.unlink()
            return True
        except Exception as exc:
            logger.error("Secure delete failed for %s: %s", file_path, exc)
            return False


__all__ = ["SecurityService"] 