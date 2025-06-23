from core.factories.transcriber_factory import TranscriberFactory
from core.interfaces.transcription import ITranscriber
from core.factories.llm_factory import LLMProviderFactory
from core.interfaces.llm_service import ILLMProvider


class DummyTrans(ITranscriber):
    async def transcribe(self, audio_path, **kwargs):
        return "dummy"

    def is_supported_format(self, file_path):
        return True


class DummyLLM(ILLMProvider):
    async def generate_completion(self, prompt, **kwargs):
        return "done"

    async def generate_note(self, transcript, **kwargs):
        return "note"


def test_factory_registration():
    tf = TranscriberFactory()
    tf.register_provider("dummy", DummyTrans)
    assert "dummy" in tf.get_supported_providers()
    inst = tf.create("dummy")
    assert isinstance(inst, DummyTrans)

    lf = LLMProviderFactory()
    lf.register_provider("dummy_llm", DummyLLM)
    assert "dummy_llm" in lf.get_supported_providers()
    llm = lf.create("dummy_llm")
    assert isinstance(llm, DummyLLM) 