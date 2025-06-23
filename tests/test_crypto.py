from pathlib import Path
import tempfile

from security import crypto as c


def test_encrypt_decrypt_roundtrip():
    key = c.get_encryption_key()
    plain = b"secret data"
    cipher = c.encrypt_data(plain, key)
    assert plain != cipher
    assert c.decrypt_data(cipher, key) == plain


def test_wav_encrypt_roundtrip(tmp_path: Path):
    # create minimal wav file (44-byte header + silence)
    import wave, os

    wav_path = tmp_path / "sample.wav"
    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"\x00" * 32000)  # 1 second silence

    key = c.get_encryption_key()
    enc_path, ok = c.encrypt_wav_file(wav_path, key)
    assert ok and Path(enc_path).exists()

    dec_path, ok = c.decrypt_to_wav(enc_path, key)
    assert ok and Path(dec_path).exists()
    # Clean temp files
    os.remove(enc_path)
    os.remove(dec_path) 