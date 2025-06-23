from src.llm.providers import OpenAIProvider, OllamaProvider

from core.interfaces.llm_service import ILLMProvider


def test_openai_provider_alias():
    assert issubclass(OpenAIProvider, ILLMProvider)


def test_ollama_provider_alias():
    assert issubclass(OllamaProvider, ILLMProvider) 