import pytest

from core.interfaces.token_service import ITokenService
from core.bootstrap import container


def _svc() -> ITokenService:
    return container.resolve(ITokenService)


def test_count_tokens_basic():
    svc = _svc()
    text = "Hello world"
    assert svc.count(text) >= 2


def test_count_tokens_empty():
    svc = _svc()
    assert svc.count("") == 0


def test_chunking_respects_limit():
    svc = _svc()
    transcript = " ".join(["word"] * 500)  # 500 words
    chunks = svc.chunk(transcript, max_chunk_tokens=50)
    assert chunks, "No chunks returned"
    for chunk in chunks:
        assert svc.count(chunk) <= 50 