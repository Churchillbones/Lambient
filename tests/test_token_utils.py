import pytest

from src.llm.utils import token as token_utils


@pytest.mark.parametrize("text", ["hello world", "", "This is a longer sentence with many words."])
def test_count_returns_int(text):
    tokens = token_utils.count(text)
    assert isinstance(tokens, int)
    assert tokens >= 0


def test_chunk_respects_token_limit():
    # Construct text long enough to require splitting even with a small limit
    text = " ".join(["word"] * 120)
    limit = 20
    chunks = token_utils.chunk(text, max_chunk_tokens=limit)

    # At least two chunks expected
    assert len(chunks) >= 2

    # Each chunk must respect token limit
    for chunk in chunks:
        assert token_utils.count(chunk) <= limit

    # Reassemble and compare word sets (order may vary slightly due to punctuation)
    original_words = text.replace(".", "").split()
    reassembled_words = " ".join(chunks).replace(".", "").split()
    assert sorted(original_words) == sorted(reassembled_words) 