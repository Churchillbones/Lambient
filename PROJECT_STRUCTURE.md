# Project Structure Documentation

**Ambient Transcription with GPT Note Creation**  
*Enterprise-grade audio transcription and AI-powered note generation system*

---

## Overview

This project is a comprehensive, enterprise-ready solution for real-time audio transcription with AI-powered note generation. The system has undergone extensive refactoring to implement modern software architecture patterns including dependency injection, provider patterns, and clean separation of concerns.

### Key Statistics
- **Total Files**: ~29,907 (including dependencies and models)
- **Python Source Files**: 142 total (96 in src/, 37 in tests/, 9 in backend/)  
- **TypeScript Files**: 5 (Angular frontend)
- **Directories**: 2,852
- **Architecture**: Provider-first, dependency injection with clean interfaces
- **Test Coverage**: Comprehensive unit, integration, and performance tests

---

## Directory Structure

### Root Level
```
├── 📁 app_data/                    # Application data and runtime files
├── 📁 backend/                     # FastAPI backend application
├── 📁 core/                        # Legacy core directory (transitional)
├── 📁 docs/                        # Documentation and architecture guides
├── 📁 ffmpeg/                      # FFmpeg binaries and documentation
├── 📁 frontend/                    # Angular frontend application
├── 📁 local_llm_models/           # Local LLM model storage
├── 📁 plans/                       # Project planning and refactoring documentation
├── 📁 src/                         # Main source code (new architecture)
├── 📁 tests/                       # Comprehensive test suite
├── 📁 Transcription documents/     # User documentation and guides
├── pyproject.toml                  # Python project configuration
├── requirements.txt                # Python dependencies
├── pytest.ini                     # Test configuration
├── mkdocs.yml                     # Documentation build configuration
└── Start_full_stack_working.bat   # Application launcher script
```

---

## Core Architecture (`src/`)

The `src/` directory contains the main application logic organized using modern software architecture principles:

### 🏗️ Core Infrastructure (`src/core/`)
```
src/core/
├── __init__.py
├── bootstrap.py                   # Dependency injection bootstrap
├── container.py                   # Service container implementation
├── exceptions.py                  # Core exception classes
├── 📁 config/                     # Configuration management
│   ├── configuration_service.py   # Main configuration service
│   └── settings.py                # Application settings
├── 📁 exceptions/                 # Exception handling
├── 📁 factories/                  # Abstract factories for service creation
│   ├── base_factory.py           # Base factory pattern
│   ├── config_factory.py         # Configuration factory
│   ├── llm_factory.py            # LLM provider factory
│   ├── streaming_factory.py      # Streaming service factory
│   └── transcriber_factory.py    # Transcription service factory
├── 📁 interfaces/                 # Contract definitions (dependency injection)
│   ├── audio_service.py          # Audio processing interface
│   ├── config_service.py         # Configuration interface
│   ├── llm_service.py            # LLM service interface
│   ├── security_service.py       # Security service interface
│   ├── streaming_service.py      # Streaming interface
│   ├── token_service.py          # Token management interface
│   └── transcription.py          # Transcription interface
├── 📁 providers/                  # External service providers
│   ├── azure_openai_provider.py  # Azure OpenAI integration
│   ├── local_llm_provider.py     # Local LLM provider
│   ├── ollama_provider.py        # Ollama integration
│   └── openai_provider.py        # OpenAI integration
└── 📁 services/                   # Core business services
    ├── audio_service.py           # Audio processing service
    ├── security_service.py       # Security and encryption
    ├── streaming_service.py      # Real-time streaming
    └── token_service.py           # API token management
```

**Purpose**: Provides the foundational infrastructure with dependency injection, service factories, and provider patterns for clean architecture.

### 🎤 Audio & Speech Recognition (`src/asr/`)
```
src/asr/
├── __init__.py
├── base.py                        # Base transcription classes
├── exceptions.py                  # ASR-specific exceptions
├── model_spec.py                  # Model specifications
├── transcription.py               # Core transcription logic
├── 📁 streaming/                  # Real-time streaming transcription
│   ├── connection_manager.py      # WebSocket connection management
│   ├── websocket.py              # WebSocket handling
│   └── 📁 handlers/               # Provider-specific streaming handlers
│       ├── azure_speech.py       # Azure Speech streaming
│       ├── vosk.py               # Vosk streaming handler
│       └── whisper.py            # Whisper streaming handler
└── 📁 transcribers/               # Transcription provider implementations
    ├── azure_speech.py           # Azure Speech Services
    ├── azure_whisper.py          # Azure Whisper integration
    ├── vosk.py                   # Vosk offline transcription
    └── whisper.py                # OpenAI Whisper
```

**Purpose**: Handles all audio transcription with support for multiple providers (Azure, OpenAI Whisper, Vosk) and real-time streaming capabilities.

### 🔊 Audio Processing (`src/audio/`)
```
src/audio/
├── __init__.py
├── audio_processing.py            # Core audio processing logic
├── recorder.py                    # Audio recording functionality
└── utils.py                       # Audio utility functions
```

**Purpose**: Provides audio capture, processing, and utility functions for the transcription pipeline.

### 🧠 LLM & AI Services (`src/llm/`)
```
src/llm/
├── __init__.py
├── embedding_service.py           # Text embeddings
├── llm_agent_enhanced.py         # Enhanced LLM agent
├── llm_integration.py            # LLM integration layer
├── prompts.py                    # Prompt templates
├── provider_utils.py             # Provider utility functions
├── routing.py                    # LLM routing logic
├── templates.py                  # Template management
├── token_management.py           # Token usage tracking
├── 📁 agents/                    # Specialized AI agents
│   ├── base.py                   # Base agent class
│   ├── clinical_writer.py       # Medical note writing
│   ├── medical_extractor.py     # Medical information extraction
│   ├── quality_reviewer.py      # Quality assurance agent
│   └── transcription_cleaner.py # Transcription cleanup
├── 📁 pipeline/                  # Processing pipelines
│   └── orchestrator.py          # Agent orchestration
├── 📁 services/                  # LLM-specific services
│   ├── api_client.py            # API client abstraction
│   ├── note_generator.py        # Note generation service
│   ├── speaker_diarizer.py      # Speaker identification
│   ├── token_manager.py         # Token management
│   └── transcription_cleaner.py # Transcription cleanup service
├── 📁 utils/                     # LLM utilities
│   └── token.py                 # Token calculation utilities
└── 📁 workflows/                 # Processing workflows
    └── traditional.py           # Traditional workflow implementation
```

**Purpose**: Manages all AI and LLM functionality including specialized agents, processing pipelines, and provider integrations for intelligent note generation.

### 🔒 Security (`src/security/`)
```
src/security/
├── __init__.py
└── crypto.py                     # Cryptographic functions
```

**Purpose**: Provides security services including encryption, key management, and secure data handling.

### 🛠️ Utilities (`src/utils/`)
```
src/utils/
├── __init__.py
├── audio.py                      # Audio-specific utilities
├── embedding.py                  # Embedding utilities
├── file.py                       # File handling utilities
├── resource.py                   # Resource management
└── text.py                       # Text processing utilities
```

**Purpose**: Common utility functions used across the application.

---

## Backend API (`backend/`)

FastAPI-based REST API with WebSocket support:

```
backend/
├── __init__.py
├── main.py                       # FastAPI application entry point
├── realtime.py                   # Real-time WebSocket endpoints
└── 📁 routers/                   # API route modules
    ├── __init__.py
    ├── asr.py                    # Transcription API endpoints
    └── streaming_ws.py           # WebSocket streaming endpoints
```

**Key Features**:
- RESTful API design
- WebSocket support for real-time transcription
- CORS configuration for frontend integration
- Dependency injection integration
- Modular router architecture

---

## Frontend Application (`frontend/`)

Modern Angular application with TypeScript:

```
frontend/
├── README.md
├── angular.json                  # Angular CLI configuration
├── package.json                  # Node.js dependencies
├── proxy.conf.json              # Development proxy configuration
├── tsconfig.json                # TypeScript configuration
├── 📁 src/
│   ├── index.html               # Main HTML template
│   ├── main.ts                  # Application bootstrap
│   ├── polyfills.ts            # Browser compatibility
│   ├── styles.css              # Global styles
│   └── 📁 app/                  # Angular application
│       ├── app.component.ts     # Main app component
│       ├── app.component.html   # Main app template
│       ├── app.component.css    # Main app styles
│       ├── app.module.ts        # App module configuration
│       └── transcription.service.ts  # Transcription service
└── 📁 dist/                     # Built application (generated)
```

**Technology Stack**:
- Angular 17.x
- TypeScript 5.2
- RxJS for reactive programming
- WebSocket integration for real-time features

---

## Test Suite (`tests/`)

Comprehensive testing infrastructure with multiple test types:

```
tests/
├── __init__.py
├── conftest.py                   # Pytest configuration
├── 📁 fixtures/                  # Test data and fixtures
│   ├── audio_samples/           # Sample audio files
│   ├── configuration_data.py    # Config test data
│   └── transcription_data.py    # Transcription test data
├── 📁 integration/               # Integration tests
│   ├── test_agent_workflow.py   # End-to-end agent tests
│   ├── test_services.py        # Service integration tests
│   ├── test_streaming_workflow.py  # Streaming tests
│   └── test_transcription_pipeline.py  # Pipeline tests
├── 📁 mocks/                     # Mock implementations
│   ├── azure_openai_mock.py    # Azure OpenAI mocks
│   ├── azure_speech_mock.py    # Azure Speech mocks
│   ├── ollama_mock.py          # Ollama mocks
│   └── vosk_mock.py            # Vosk mocks
├── 📁 performance/               # Performance tests
│   └── test_streaming_performance.py
├── 📁 unit/                      # Unit tests
│   ├── test_audio_service.py    # Audio service tests
│   ├── test_llm_services.py    # LLM service tests
│   └── test_streaming_service.py  # Streaming service tests
└── [various test files]         # Specific feature tests
```

**Test Categories**:
- **Unit Tests**: Individual component testing
- **Integration Tests**: Service interaction testing
- **Performance Tests**: Load and performance validation
- **Mock Infrastructure**: Comprehensive mocking for external services

---

## Application Data (`app_data/`)

Runtime data and configuration storage:

```
app_data/
├── 📁 cache/                     # Application cache
├── 📁 keys/                      # Security keys and certificates
├── 📁 logs/                      # Application logs
├── 📁 models/                    # Downloaded ML models
│   └── vosk-model-en-us-0.22/   # Vosk speech recognition model
├── 📁 notes/                     # Generated notes storage
├── 📁 whisper_models/            # Whisper model files
│   ├── base.pt
│   ├── medium.pt
│   └── tiny.pt
└── prompt_templates.json         # AI prompt templates
```

---

## Documentation (`docs/`)

Technical documentation and guides:

```
docs/
├── architecture.md               # System architecture overview
├── index.md                     # Documentation index
└── 📁 usage/
    └── providers.md             # Provider usage guide
```

---

## Configuration Files

### Python Configuration
- **`pyproject.toml`**: Modern Python project configuration with Black, Ruff linting
- **`requirements.txt`**: Production dependencies
- **`pytest.ini`**: Test framework configuration

### Frontend Configuration
- **`angular.json`**: Angular CLI and build configuration
- **`package.json`**: Node.js dependencies and scripts
- **`tsconfig.json`**: TypeScript compiler configuration

### Documentation
- **`mkdocs.yml`**: Documentation site configuration

---

## Architecture Highlights

### 🏗️ Dependency Injection Architecture
- **ServiceContainer**: Lightweight DI container with singleton lifecycle management
- **Interface-based Design**: All services implement clear contracts
- **Factory Pattern**: Providers created through factories for flexibility
- **Bootstrap System**: Centralized service registration and initialization

### 🔄 Provider Pattern Implementation
- **LLM Providers**: Azure OpenAI, OpenAI, Ollama, Local LLM support
- **Transcription Providers**: Whisper, Vosk, Azure Speech Services
- **Streaming Providers**: Real-time audio processing for all transcription engines
- **Security Providers**: Encryption and key management

### 🎯 Clean Architecture Principles
- **Separation of Concerns**: Clear boundaries between layers
- **Interface Segregation**: Focused, single-purpose interfaces
- **Dependency Inversion**: High-level modules don't depend on low-level modules
- **Single Responsibility**: Each class has one reason to change

### 🔧 Enterprise Features
- **Comprehensive Testing**: Unit, integration, and performance tests
- **Security**: Encryption, secure key storage, input sanitization
- **Monitoring**: Token usage tracking, performance monitoring
- **Scalability**: Modular architecture supports horizontal scaling
- **Maintainability**: Clean code practices, comprehensive documentation

---

## Service Layer Organization

### Core Services
- **AudioService**: Audio capture, processing, and format conversion
- **StreamingService**: Real-time audio streaming and WebSocket management
- **TokenService**: API token management and usage tracking
- **SecurityService**: Encryption, decryption, and secure storage

### LLM Services
- **NoteGenerator**: AI-powered note generation from transcriptions
- **TranscriptionCleaner**: Intelligent cleanup and formatting
- **SpeakerDiarizer**: Speaker identification and separation
- **AgentOrchestrator**: Multi-agent workflow coordination

### Transcription Services
- **WhisperTranscriber**: OpenAI Whisper integration
- **VoskTranscriber**: Offline speech recognition
- **AzureSpeechTranscriber**: Azure Cognitive Services
- **StreamingHandlers**: Real-time transcription processing

---

## Technology Stack

### Backend
- **Python 3.11+**: Core runtime
- **FastAPI**: Modern web framework
- **Uvicorn**: ASGI server
- **PyAudio**: Audio capture
- **Cryptography**: Security services
- **PyTorch**: Machine learning models

### Frontend
- **Angular 17**: Modern web framework
- **TypeScript**: Type-safe JavaScript
- **RxJS**: Reactive programming
- **WebSocket**: Real-time communication

### AI/ML
- **OpenAI Whisper**: Speech-to-text
- **Vosk**: Offline speech recognition
- **OpenAI GPT**: Language model integration
- **Azure Cognitive Services**: Cloud AI services
- **Ollama**: Local LLM support

### Testing
- **Pytest**: Testing framework
- **Mock**: Service mocking
- **Coverage**: Code coverage analysis

---

## Deployment Architecture

The system supports multiple deployment scenarios:
- **Development**: Local development with hot reload
- **Production**: Container-based deployment with reverse proxy
- **Hybrid**: On-premises with cloud AI services
- **Offline**: Complete offline operation with local models

---

This project structure represents a mature, enterprise-grade application with modern software architecture patterns, comprehensive testing, and production-ready deployment capabilities. The refactoring phases have successfully transformed the codebase into a maintainable, scalable, and extensible system suitable for enterprise deployment.