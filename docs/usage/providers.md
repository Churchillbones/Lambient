# Using Providers

Providers encapsulate third-party SDKs. Swap vendors via config – no code changes.

```python
from core.factories import LLMProviderFactory

factory = container.resolve(LLMProviderFactory)
provider = factory.create("openai", api_key="...", model="gpt-4o")

completion = await provider.generate_completion("Summarise this …")
print(completion)
```

Available IDs:

| ID | Class |
|-----|--------------------------|
| `azure_openai` | `AzureOpenAIProvider` |
| `openai` | `OpenAIProvider` |
| `local` | `LocalLLMProvider` |
| `ollama` | `OllamaProvider` | 