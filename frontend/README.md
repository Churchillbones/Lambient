# Medical Transcription Frontend

This Angular application provides a comprehensive medical transcription and note generation interface.

## Features

### 🎙️ Audio Recording
- Real-time audio recording with visual feedback
- Traditional and real-time transcription modes
- Recording timer and controls (start, pause, stop)
- Patient consent documentation

### 📁 File Upload
- Drag-and-drop audio file upload
- Support for WAV, MP3, and M4A formats
- File size display and validation

### 🔧 Configuration
- Configurable ASR engines (Vosk, Whisper, Azure Speech)
- Azure OpenAI integration settings
- Model selection for different transcription engines
- Security settings including encryption options

### 📝 Transcription Processing
- Multi-step processing workflow with progress indicators
- Raw transcription display
- Transcription cleaning and correction
- Speaker diarization (simulated)
- Medical note generation using GPT models

### 🔄 Model Comparison
- Side-by-side comparison of different ASR models
- Performance metrics and accuracy comparison

### 💾 Export & Download
- Copy transcriptions to clipboard
- Download individual results as text files
- Export complete session data as JSON

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm start
   ```

3. Open your browser to `http://localhost:4200`

## Configuration

The application stores configuration in localStorage and includes:

- **Azure OpenAI Settings**: API key and endpoint configuration
- **ASR Engine Selection**: Choose between Vosk, Whisper, or Azure Speech
- **Model Selection**: Different model sizes and types
- **Security Options**: Encryption settings for recordings

## API Integration

The frontend integrates with the FastAPI backend through:

- `/api/transcribe` - Audio transcription endpoint
- `/api/notes` - Medical note generation endpoint
- `/api/templates` - Template management endpoint

## Browser Requirements

- Modern browser with MediaRecorder API support
- Microphone access permissions for recording
- Clipboard API support for copy functionality

## Development

The application is built with:
- Angular 17
- TypeScript
- RxJS for reactive programming
- Font Awesome for icons
- CSS custom properties for theming
