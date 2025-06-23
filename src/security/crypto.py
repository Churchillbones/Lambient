from __future__ import annotations

"""Encryption / decryption helpers.

This module hosts all cryptographic utilities that were formerly located in
*src/encryption.py*.  It is intentionally self-contained so it can be easily
unit-tested and reused by other packages.

Public API (re-exported via *src.security*):
    • get_encryption_key
    • encrypt_data / decrypt_data
    • encrypt_wav_file / decrypt_to_wav
    • secure_audio_processing (context-manager)
"""

from contextlib import contextmanager
from functools import lru_cache
import json
import logging
import tempfile
import wave
from pathlib import Path
from typing import Tuple, Iterator

from cryptography.fernet import Fernet

from ..core.container import global_container
from ..core.interfaces.config_service import IConfigurationService

logger = logging.getLogger("ambient_scribe")

# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------

def _config() -> dict[str, Path]:
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

# ---------------------------------------------------------------------------
# Key management
# ---------------------------------------------------------------------------

@lru_cache(maxsize=None)
def get_encryption_key() -> bytes:
    """Return a Fernet key; generate one if not present on disk."""
    conf = _config()
    conf["key_dir"].mkdir(parents=True, exist_ok=True)
    key_file = conf["key_dir"] / "encryption_key.bin"
    if not key_file.exists():
        key = Fernet.generate_key()
        key_file.write_bytes(key)
        logger.info("Generated new encryption key at %s", key_file)
        return key
    key = key_file.read_bytes()
    if len(key) != 44:  # Fernet key is 32 bytes base64 => 44 ascii chars
        logger.warning("Encryption key %s has unexpected length %s", key_file, len(key))
    return key

# ---------------------------------------------------------------------------
# Primitive encryption helpers
# ---------------------------------------------------------------------------

def encrypt_data(data: bytes, key: bytes) -> bytes:  # noqa: D401
    try:
        return Fernet(key).encrypt(data)
    except Exception as exc:  # pragma: no cover – cryptography error
        logger.error("Encryption failed: %s", exc)
        raise ValueError("Encryption failed") from exc


def decrypt_data(cipher: bytes, key: bytes) -> bytes:  # noqa: D401
    try:
        return Fernet(key).decrypt(cipher)
    except Exception as exc:  # pragma: no cover
        logger.error("Decryption failed: %s", exc)
        raise ValueError("Decryption failed") from exc

# ---------------------------------------------------------------------------
# WAV helpers
# ---------------------------------------------------------------------------

def encrypt_wav_file(wav_path: str | Path, key: bytes) -> Tuple[str, bool]:  # noqa: D401
    """Encrypt *wav_path* and save alongside as ``.enc`` custom file."""
    wav_path = str(wav_path)
    try:
        with wave.open(wav_path, "rb") as wf:
            meta = {
                "channels": wf.getnchannels(),
                "sampwidth": wf.getsampwidth(),
                "framerate": wf.getframerate(),
                "nframes": wf.getnframes(),
            }
            frames = wf.readframes(meta["nframes"])
    except wave.Error as exc:
        logger.error("Error reading WAV file %s: %s", wav_path, exc)
        return wav_path, False

    cipher = encrypt_data(frames, key)
    meta["encrypted"] = True
    meta_json = json.dumps(meta).encode()

    enc_path = str(Path(wav_path).with_suffix(".enc"))
    with open(enc_path, "wb") as fh:
        fh.write(b"MENC")  # magic
        fh.write((1).to_bytes(4, "little"))  # version
        fh.write(len(meta_json).to_bytes(4, "little"))
        fh.write(meta_json)
        fh.write(cipher)

    logger.info("Encrypted audio saved to %s", enc_path)
    return enc_path, True


def decrypt_to_wav(enc_path: str | Path, key: bytes) -> Tuple[str, bool]:  # noqa: D401
    """Decrypt *.enc* back to a temp *.wav* file."""
    enc_path = str(enc_path)
    with open(enc_path, "rb") as fh:
        if fh.read(4) != b"MENC":
            raise ValueError("Invalid encrypted audio file")
        version = int.from_bytes(fh.read(4), "little")
        if version != 1:
            raise ValueError("Unsupported encryption version: %s" % version)
        meta_len = int.from_bytes(fh.read(4), "little")
        meta = json.loads(fh.read(meta_len))
        cipher = fh.read()

    frames = decrypt_data(cipher, key)
    conf = _config()
    conf["cache_dir"].mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav", dir=conf["cache_dir"]) as tmp:
        wav_tmp = tmp.name

    with wave.open(wav_tmp, "wb") as wf:
        wf.setnchannels(meta["channels"])
        wf.setsampwidth(meta["sampwidth"])
        wf.setframerate(meta["framerate"])
        wf.writeframes(frames)

    return wav_tmp, True

# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------

@contextmanager
def secure_audio_processing(audio_path: str, use_encryption: bool) -> Iterator[str]:
    """Yield a path to an audio file, encrypting & decrypting transparently."""
    if not use_encryption:
        yield audio_path
        return

    key = get_encryption_key()
    enc_path, ok = encrypt_wav_file(audio_path, key)
    if not ok:
        logger.warning("Encryption failed; processing unencrypted audio")
        yield audio_path
        return

    dec_path, ok = decrypt_to_wav(enc_path, key)
    if not ok:
        logger.warning("Decryption failed; processing unencrypted audio")
        yield audio_path
        return

    try:
        yield dec_path
    finally:
        Path(dec_path).unlink(missing_ok=True)

__all__ = [
    "get_encryption_key",
    "encrypt_data",
    "decrypt_data",
    "encrypt_wav_file",
    "decrypt_to_wav",
    "secure_audio_processing",
] 