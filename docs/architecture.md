# Architecture Overview

The application follows a **provider-first** architecture.

```mermaid
flowchart TD
    UI["Angular Frontend"] -->|REST| API["FastAPI Backend"]
    API -->|DI resolve| Factory["LLMProviderFactory"]
    API -->|DI resolve| TFactory["TranscriberFactory"]
    Factory --> Azure["AzureOpenAIProvider"]
    Factory --> OpenAI["OpenAIProvider"]
    Factory --> Ollama["OllamaProvider"]
    TFactory --> Whisper["WhisperTranscriber"]
    TFactory --> Vosk["VoskTranscriber"]
    TFactory --> AzureSTT["AzureSpeechTranscriber"]
    subgraph Core Services
        TokenService["OpenAITokenService"]
    end
    API --> TokenService
```

### Key Principles
* **No business code imports SDKs directly** – always go through a provider.
* **Factories + DI container** give runtime flexibility.
* **Token management** centralized under `ITokenService`. 