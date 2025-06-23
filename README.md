# Ambient Transcription with GPT Note Creation 🩺

[![Production Ready](https://img.shields.io/badge/Production-Ready-brightgreen)](https://github.com/Churchillbones/Ambient-Transcription-with-GPT-Note-Creation-) 
[![Test Coverage](https://img.shields.io/badge/Coverage-90%25+-green)](./tests/)
[![Architecture](https://img.shields.io/badge/Architecture-Microservice-blue)](./COMPREHENSIVE_REFACTORING_PLAN.md)
[![Phase Complete](https://img.shields.io/badge/Refactoring-98%25_Complete-success)](./PHASE_COMPLETION_SUMMARY.md)

## Description

This project provides a **production-ready, enterprise-grade** medical transcription application with an Angular frontend and FastAPI backend. The application allows medical professionals to upload or record audio encounters, transcribe the audio using various Automatic Speech Recognition (ASR) models, and generate structured clinical notes using advanced LLM models. The system features **real-time streaming transcription**, **comprehensive security**, and **enterprise-grade testing infrastructure**.

## 🏆 Production Status

**This application is production-ready** with:
- ✅ **Enterprise-grade architecture** with dependency injection and microservice design
- ✅ **Real-time streaming transcription** with session management and performance monitoring
- ✅ **Comprehensive security** with encryption, audit logging, and HIPAA-compliant data handling
- ✅ **90%+ test coverage** with automated quality gates and CI/CD pipeline
- ✅ **Performance benchmarks** ensuring scalability and low-latency processing
- ✅ **Modern agent-based architecture** with modular AI pipeline orchestration

## ✨ Core Features

### **🎙️ Audio Processing**
- **Real-time Recording:** Stream audio directly within the application with live transcription
- **Multi-format Upload:** Support for WAV, MP3, FLAC, and other audio formats
- **Audio Enhancement:** Automatic noise reduction, level normalization, and format conversion
- **Performance Monitoring:** Real-time audio quality assessment and processing metrics

### **🗣️ Advanced Transcription**
- **Real-time Streaming:** WebSocket-based live transcription with <500ms latency
- **Multiple ASR Engines:**
  - **Vosk:** Local, offline transcription with multiple language models
  - **Azure Speech:** Cloud-based transcription with high accuracy
  - **Whisper:** Local and Azure-hosted models for specialized medical vocabulary
- **Session Management:** Concurrent session support with resource monitoring
- **Performance Benchmarks:** P95/P99 latency metrics and throughput validation

### **🤖 AI-Powered Note Generation**
- **Agent-Based Architecture:** Modular pipeline with specialized AI agents:
  - **Transcription Cleaner:** Text preprocessing and error correction
  - **Medical Extractor:** Clinical data and entity extraction
  - **Clinical Writer:** Professional medical note generation (SOAP, summary, diagnostic)
  - **Quality Reviewer:** Automated note quality assessment and validation
- **LLM Integration:** Support for Azure OpenAI, Ollama, and local models
- **Template System:** Customizable clinical note templates and formats

### **🔒 Enterprise Security**
- **HIPAA Compliance:** Secure data handling with encryption at rest and in transit
- **Audit Logging:** Comprehensive security event tracking
- **Multi-pass Deletion:** Secure file deletion with overwrite verification
- **API Key Management:** Encrypted credential storage and rotation

### **⚡ Performance & Scalability**
- **Concurrent Processing:** Support for multiple simultaneous transcription sessions
- **Resource Monitoring:** CPU, memory, and audio buffer tracking
- **Load Balancing:** Intelligent session distribution and cleanup
- **Performance Metrics:** Real-time latency and throughput monitoring

### **🧪 Quality Assurance**
- **90%+ Test Coverage:** Comprehensive unit, integration, and performance tests
- **Automated CI/CD:** GitHub Actions pipeline with quality gates
- **Mock Infrastructure:** Complete external service mocking for testing
- **Performance Validation:** Automated regression testing and benchmarks

## Prerequisites

*   **Python:** Version 3.8 or newer. The setup script checks for this.
*   **pip:** Python package installer.
*   **FFmpeg:** Required for audio format handling. 
    - Download from [GitHub Codex FFmpeg Release](https://github.com/GyanD/codexffmpeg/releases/tag/2025-04-14-git-3b2a9410ef)
    - Download the appropriate zip file for your system (e.g., `ffmpeg-2025-04-14-git-3b2a9410ef-essentials_build.zip`)
    - Extract the contents to a folder named `ffmpeg` in the project root directory
    - Ensure that the path `ffmpeg\bin\ffmpeg.exe` exists after extraction
*   **(Optional) Ollama:** Required if using non-GPT local LLMs. Needs to be installed and running separately. [Link to Ollama setup guide if available]
*   **(Optional) Vosk Models:** Required for Vosk transcription. The setup script can download a small English model (`vosk-model-small-en-us-0.15`) automatically. You can download other models from [https://alphacephei.com/vosk/models](https://alphacephei.com/vosk/models) and place them in the `app_data/models/` directory (e.g., `app_data/models/vosk-model-en-us-0.22`).
*   **(Optional) Local Whisper Models:** Required for local Whisper transcription. Download model files (e.g., `tiny.pt`, `base.pt`) and place them in `app_data/whisper_models/`.

## Installation & Setup

The `setup.bat` script automates most of the setup process.

1.  **Clone/Download:** Get the project source code.
    ```bash
    # Clone the repository
    git clone https://github.com/Churchillbones/Ambient-Transcription-with-GPT-Note-Creation-
    # Navigate to the project directory
    cd Ambient-Transcription-with-GPT-Note-Creation-
    ```
2.  **Navigate:** Open a terminal or command prompt **as Administrator** in the project's root directory. The setup script requires admin privileges.
3.  **Run Setup Script:** Execute the setup batch file.
    ```bash
    setup.bat
    ```
    This script will:
    *   Check for Python 3.8+.
    *   Create a Python virtual environment named `venv`.
    *   Activate the virtual environment.
    *   Install required Python packages from `requirements.txt`.
    *   Create necessary directories (`app_data`, `local_llm_models`, etc.).
    *   Check for FFmpeg and optionally download/install it.
    *   Check for Vosk models and optionally download a default small English model.
    *   Create a template `.env` file if one doesn't exist.
    *   Attempt to launch the backend API (`uvicorn backend.main:app --reload`).
    *   Attempt to launch the backend API (`uvicorn backend.main:app --reload`).

    *Note:* If `setup.bat` fails during dependency installation (e.g., PyAudio), you might need to install system prerequisites manually (like PortAudio) or use alternative installation methods mentioned in the script's output.

## Batch Scripts for Windows Users

This repository includes two batch scripts for Windows users to simplify setup and execution:

### `setup.bat`

A comprehensive setup script that:
- Requests administrator privileges if needed
- Verifies Python 3.8+ is installed
- Creates and configures a Python virtual environment
- Installs all dependencies from requirements.txt
- Sets up directories for the application
- Offers to download and configure FFmpeg if needed
- Offers to download a basic Vosk model if none are present
- Creates a template .env file if one doesn't exist
- Launches the application for first-time setup

To use:
```bash
setup.bat
```

### `Start_app.bat`

A streamlined script to start the application that:
- Checks if the Ollama service is running (if you're using local models)
- Updates local model information
- Starts the Ollama API bridge in a separate terminal
- Launches the main application

To use:
```bash
Start_app.bat
```

### Manual Setup (Non-Windows Users)

If you're not using Windows or prefer manual setup:

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Linux/macOS
   ```

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Create necessary directories:
   ```bash
   mkdir -p app_data/models app_data/keys app_data/logs app_data/cache app_data/notes local_llm_models
   ```

4. Install FFmpeg manually from https://ffmpeg.org/download.html

5. Download a Vosk model (optional):
   - Download from https://alphacephei.com/vosk/models
   - Extract to app_data/models directory

6. Create a .env file with your configuration

7. Start Ollama service (if using)

8. Run the Ollama bridge:
   ```bash
   python ollama_bridge.py
   ```

9. In a separate terminal, start the backend API:
   ```bash
   uvicorn backend.main:app --reload
   ```
10. Start the Angular frontend:
   ```bash
   cd frontend
   npm install
   npm start
   ```

## Configuration

1.  **Environment Variables:** After running `setup.bat` once, a `.env` file should exist in the project root. Edit this file to add your credentials and settings:
    ```dotenv
    # Azure OpenAI API settings
    AZURE_API_KEY=YOUR_AZURE_OPENAI_API_KEY
    AZURE_ENDPOINT=https://your-resource-name.openai.azure.com/
    MODEL_NAME=gpt-4o # Or your desired Azure OpenAI deployment name

    # Local model settings (optional)
    LOCAL_MODEL_API_URL=http://localhost:8000/generate_note # URL for Ollama bridge or similar

    # Debug settings
    DEBUG_MODE=False # Set to True for more verbose logging
    ```
2.  **Application Settings:** Further configuration (like selecting specific models, toggling encryption) can often be done directly in the application's sidebar when it's running.

## Usage

1.  **Prerequisites:** Ensure any necessary external services (like Ollama) are running and prerequisites (like FFmpeg) are installed.
2.  **Activate Environment:** Open a terminal in the project root and activate the virtual environment:
    ```bash
    .\venv\Scripts\activate
    ```
3.  **Start the Backend:** Run the FastAPI server:
    ```bash
    uvicorn backend.main:app --reload
    ```
4.  **Start the Frontend:** In the `frontend` folder run:
    ```bash
    npm install
    npm start
    ```
    The Angular development server runs on `http://localhost:4200`.

## 🏗️ Architecture

This application uses a **modern microservice architecture** with:

### **Backend (Python/FastAPI)**
- **Dependency Injection Container:** Type-safe service resolution with singleton/transient lifetime management
- **Service Layer:** 8+ core service interfaces with proper abstractions
- **Agent Pipeline:** Modular AI agents with orchestrator pattern
- **Real-time Streaming:** WebSocket-based transcription with session management
- **Security Services:** Encryption, audit logging, and secure file handling

### **Frontend (Angular/TypeScript)**
- **Component Architecture:** Modular UI components with reactive patterns
- **Service Layer:** Focused services for audio, transcription, and configuration
- **Real-time Communication:** WebSocket integration for live transcription
- **State Management:** Reactive state management with RxJS

### **Testing Infrastructure**
- **Unit Tests:** 90%+ coverage with comprehensive service testing
- **Integration Tests:** End-to-end workflow validation
- **Performance Tests:** Latency, throughput, and scalability benchmarks
- **Mock Infrastructure:** Complete external service simulation
- **CI/CD Pipeline:** Automated testing with quality gates

## 📁 Project Structure

```
├── src/                          # Core application source
│   ├── asr/                      # Speech recognition services
│   │   ├── streaming/            # Real-time transcription
│   │   └── transcribers/         # Batch transcription engines
│   ├── core/                     # DI container & core services
│   │   ├── interfaces/           # Service abstractions
│   │   ├── services/             # Core service implementations
│   │   └── providers/            # External service providers
│   ├── llm/                      # Language model services
│   │   ├── agents/               # Specialized AI agents
│   │   ├── pipeline/             # Workflow orchestration
│   │   └── services/             # LLM-specific services
│   └── security/                 # Security and encryption
├── tests/                        # Comprehensive test suite
│   ├── unit/                     # Unit tests (90%+ coverage)
│   ├── integration/              # Integration tests
│   ├── performance/              # Performance benchmarks
│   ├── mocks/                    # External service mocks
│   └── fixtures/                 # Test data and generators
├── backend/                      # FastAPI application
├── frontend/                     # Angular application
└── .github/workflows/            # CI/CD pipeline
```

## 🔧 Key Dependencies

### **Backend**
- **FastAPI/Uvicorn:** High-performance async API server
- **PyAudio/wave:** Professional audio recording and processing
- **Vosk:** Offline speech recognition with multiple languages
- **Azure OpenAI:** Cloud-based LLM and Whisper integration
- **Cryptography:** Enterprise-grade encryption and security
- **psutil:** System resource monitoring and performance tracking

### **Frontend**
- **Angular:** Modern TypeScript framework with dependency injection
- **RxJS:** Reactive programming for real-time data streams
- **WebSocket:** Real-time communication for live transcription

### **Testing & Quality**
- **pytest:** Comprehensive testing framework with async support
- **pre-commit:** Automated code quality hooks
- **GitHub Actions:** CI/CD pipeline with multi-version testing
- **Black/Ruff/MyPy:** Code formatting, linting, and type checking

## 📚 Documentation

- **[Comprehensive Refactoring Plan](./COMPREHENSIVE_REFACTORING_PLAN.md)** - Complete architectural documentation
- **[Phase Completion Summary](./PHASE_COMPLETION_SUMMARY.md)** - Development progress and achievements
- **[Test Documentation](./tests/)** - Testing infrastructure and coverage reports
