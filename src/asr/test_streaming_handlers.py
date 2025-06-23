import sys
import queue
from unittest import mock

# ---------------------------------------------------------------------------
# Provide lightweight stubs for optional heavy dependencies so tests run fast
# ---------------------------------------------------------------------------
class _DummyRecognizer:
    def __init__(self, *_, **__):
        self._called = False

    def AcceptWaveform(self, *_):
        # Pretend to accept first chunk as final, then partial
        first = not self._called
        self._called = True
        return first

    def Result(self):
        return '{"text": "hello", "result": []}'

    def PartialResult(self):
        return '{"partial": "he"}'

    def SetWords(self, *_):
        pass


class _DummyVoskModule(mock.MagicMock):
    Model = mock.MagicMock(return_value="model")
    KaldiRecognizer = _DummyRecognizer


class _DummyWhisperModule(mock.MagicMock):
    def load_model(self, *_, **__):
        class _M:
            def transcribe(self, *_a, **_kw):
                return {"text": "hello"}

        return _M()


class _DummyResponse:
    status_code = 200

    def json(self):
        return {"RecognitionStatus": "Success", "DisplayText": "hi"}

    text = "OK"


# Inject stubs into sys.modules
sys.modules.setdefault("vosk", _DummyVoskModule())
sys.modules.setdefault("whisper", _DummyWhisperModule())
requests_mock = mock.MagicMock()
requests_mock.post.return_value = _DummyResponse()
sys.modules.setdefault("requests", requests_mock)

# ---------------------------------------------------------------------------
# Import handlers (after stubs in place)
# ---------------------------------------------------------------------------
from src.asr.streaming import (
    VoskStreamingHandler,
    WhisperStreamingHandler,
    AzureSpeechStreamingHandler,
)


def _run_handler(handler):
    handler.update_queue.put = handler.update_queue.put  # type: ignore[attr-defined]
    handler(b"\x00\x00")  # send tiny dummy chunk
    # Ensure at least one entry queued
    assert not handler.update_queue.empty()


def test_vosk_streaming_handler():
    q = queue.Queue()
    h = VoskStreamingHandler(model_path="/dummy/path", update_queue=q)
    _run_handler(h)


def test_whisper_streaming_handler():
    q = queue.Queue()
    h = WhisperStreamingHandler(model_size="tiny", update_queue=q)
    _run_handler(h)


def test_azure_streaming_handler():
    q = queue.Queue()
    h = AzureSpeechStreamingHandler(api_key="k", endpoint="https://e", update_queue=q)
    # call twice to force send condition
    h(b"\x00\x00")
    h.last_time -= 4  # force processing path
    h(b"\x00\x00")
    assert not q.empty() 