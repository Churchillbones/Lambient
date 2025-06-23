from core.bootstrap import container
from core.factories.llm_factory import LLMProviderFactory
from core.factories.transcriber_factory import TranscriberFactory


def test_llm_factory_supported():
    factory = container.resolve(LLMProviderFactory)
    supported = factory.get_supported_providers()
    # Expect at least the defaults
    for provider in ["azure_openai", "openai", "local", "ollama"]:
        assert provider in supported


def test_llm_factory_create_local():
    factory = container.resolve(LLMProviderFactory)
    provider = factory.create("local")  # Uses defaults
    note = "dummy"
    # Should not raise and return string (empty from stub).
    assert hasattr(provider, "generate_note")


def test_transcriber_factory_supported():
    tf = container.resolve(TranscriberFactory)
    providers = tf.get_supported_providers()
    for prov in ["vosk", "whisper", "azure_speech"]:
        assert prov in providers 