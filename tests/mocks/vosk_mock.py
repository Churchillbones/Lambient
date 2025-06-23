"""Mock Vosk service for testing."""

import asyncio
import json
import random
from typing import Dict, Any, List, Optional
from unittest.mock import MagicMock
import tempfile
import os


class MockVoskResult:
    """Mock result object for Vosk recognition."""
    
    def __init__(self, text: str, confidence: float = 0.9, is_partial: bool = False):
        self.text = text
        self.confidence = confidence
        self.is_partial = is_partial
        self.words = self._generate_word_level_data(text, confidence)
    
    def _generate_word_level_data(self, text: str, confidence: float) -> List[Dict[str, Any]]:
        """Generate mock word-level timing and confidence data."""
        words = text.split()
        word_data = []
        current_time = 0.0
        
        for word in words:
            word_duration = random.uniform(0.2, 0.8)  # Random word duration
            word_confidence = confidence + random.uniform(-0.1, 0.1)  # Slight variance
            word_confidence = max(0.0, min(1.0, word_confidence))  # Clamp to [0,1]
            
            word_data.append({
                "conf": word_confidence,
                "end": current_time + word_duration,
                "start": current_time,
                "word": word
            })
            
            current_time += word_duration + random.uniform(0.05, 0.15)  # Gap between words
        
        return word_data
    
    def as_dict(self) -> Dict[str, Any]:
        """Return result as dictionary (Vosk format)."""
        if self.is_partial:
            return {
                "partial": self.text
            }
        else:
            return {
                "text": self.text,
                "result": self.words
            }


class MockVoskModel:
    """Mock Vosk model for testing."""
    
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.language = self._extract_language_from_path(model_path)
        self._is_loaded = True
    
    def _extract_language_from_path(self, path: str) -> str:
        """Extract language from model path."""
        if "en" in path.lower():
            return "en"
        elif "es" in path.lower():
            return "es"
        elif "fr" in path.lower():
            return "fr"
        elif "de" in path.lower():
            return "de"
        else:
            return "en"  # Default
    
    def get_language(self) -> str:
        """Get model language."""
        return self.language
    
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._is_loaded


class MockVoskRecognizer:
    """Mock Vosk recognizer for testing."""
    
    def __init__(self, model: MockVoskModel, sample_rate: int = 16000):
        self.model = model
        self.sample_rate = sample_rate
        self.partial_results: List[str] = []
        self.recognition_count = 0
        self._audio_buffer = b""
        self._generate_partials = True
    
    def accept_waveform(self, audio_data: bytes) -> bool:
        """Process audio data and return True if final result is ready."""
        self._audio_buffer += audio_data
        self.recognition_count += 1
        
        # Simulate partial results every few chunks
        if self._generate_partials and len(self._audio_buffer) > 1000:
            return False  # Still processing
        
        # Simulate final result after sufficient audio
        return len(self._audio_buffer) > 5000
    
    def partial_result(self) -> str:
        """Get partial recognition result."""
        # Generate partial text based on audio buffer length
        partial_text = self._generate_partial_text()
        self.partial_results.append(partial_text)
        
        result = MockVoskResult(partial_text, confidence=0.7, is_partial=True)
        return json.dumps(result.as_dict())
    
    def result(self) -> str:
        """Get final recognition result."""
        # Generate final text based on accumulated audio
        final_text = self._generate_final_text()
        
        result = MockVoskResult(final_text, confidence=0.9, is_partial=False)
        return json.dumps(result.as_dict())
    
    def final_result(self) -> str:
        """Get the absolute final result."""
        return self.result()
    
    def _generate_partial_text(self) -> str:
        """Generate partial transcription text."""
        partial_phrases = [
            "The patient",
            "The patient says",
            "The patient says they feel",
            "The patient says they feel unwell today"
        ]
        
        # Return progressively longer partial results
        index = min(len(self.partial_results), len(partial_phrases) - 1)
        return partial_phrases[index]
    
    def _generate_final_text(self) -> str:
        """Generate final transcription text based on audio buffer."""
        # Base phrases for medical content
        medical_phrases = [
            "The patient reports feeling unwell for the past few days",
            "Doctor examines the patient and notes vital signs are stable",
            "Patient describes pain as sharp and intermittent",
            "Medical history reveals no significant prior conditions",
            "Treatment plan includes medication and follow-up in one week",
            "Patient understands the diagnosis and treatment recommendations",
            "Follow-up appointment scheduled for next week"
        ]
        
        # Generate text based on buffer size (longer audio = more text)
        buffer_size = len(self._audio_buffer)
        num_phrases = max(1, min(buffer_size // 2000, len(medical_phrases)))
        
        selected_phrases = random.sample(medical_phrases, num_phrases)
        return ". ".join(selected_phrases) + "."
    
    def reset(self):
        """Reset recognizer state."""
        self._audio_buffer = b""
        self.partial_results.clear()
        self.recognition_count = 0


class MockVoskTranscriber:
    """Mock Vosk transcriber that mimics the real transcriber interface."""
    
    def __init__(self, model_path: Optional[str] = None, sample_rate: int = 16000):
        self.model_path = model_path or "/mock/vosk/model"
        self.sample_rate = sample_rate
        self.model = MockVoskModel(self.model_path)
        self.recognizer = MockVoskRecognizer(self.model, sample_rate)
        self.transcription_history: List[Dict[str, Any]] = []
    
    async def transcribe(self, audio_file_path: str) -> str:
        """Transcribe audio file (mock)."""
        # Simulate loading audio file
        audio_size = self._get_mock_audio_size(audio_file_path)
        
        # Simulate processing time based on audio size
        processing_time = max(0.1, audio_size / 100000)  # Faster than real-time
        await asyncio.sleep(processing_time)
        
        # Generate mock audio data
        mock_audio_data = b"mock_audio" * (audio_size // 10)
        
        # Process through recognizer
        self.recognizer.accept_waveform(mock_audio_data)
        final_result_json = self.recognizer.result()
        result_data = json.loads(final_result_json)
        
        transcription = result_data.get("text", "")
        
        # Record transcription
        self.transcription_history.append({
            "file_path": audio_file_path,
            "transcription": transcription,
            "audio_size": audio_size,
            "processing_time": processing_time,
            "language": self.model.language
        })
        
        return transcription
    
    async def transcribe_stream(self, audio_data: bytes, chunk_size: int = 4000):
        """Transcribe audio stream with partial results."""
        results = []
        
        # Process audio in chunks
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i + chunk_size]
            
            # Process chunk
            has_final = self.recognizer.accept_waveform(chunk)
            
            if has_final:
                # Final result
                final_json = self.recognizer.result()
                final_data = json.loads(final_json)
                results.append({
                    "type": "final",
                    "text": final_data.get("text", ""),
                    "confidence": 0.9,
                    "words": final_data.get("result", [])
                })
                
                # Reset for next segment
                self.recognizer.reset()
            else:
                # Partial result
                partial_json = self.recognizer.partial_result()
                partial_data = json.loads(partial_json)
                results.append({
                    "type": "partial",
                    "text": partial_data.get("partial", ""),
                    "confidence": 0.7
                })
            
            # Simulate streaming delay
            await asyncio.sleep(0.1)
        
        return results
    
    def _get_mock_audio_size(self, file_path: str) -> int:
        """Get mock audio file size."""
        try:
            # If file exists, use real size
            return os.path.getsize(file_path)
        except (OSError, FileNotFoundError):
            # For testing with non-existent files, return mock size
            return random.randint(50000, 500000)
    
    def get_supported_languages(self) -> List[str]:
        """Get supported languages."""
        return ["en", "es", "fr", "de", "ru", "zh"]
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "path": self.model_path,
            "language": self.model.language,
            "sample_rate": self.sample_rate,
            "loaded": self.model.is_loaded()
        }
    
    def get_transcription_history(self) -> List[Dict[str, Any]]:
        """Get transcription history for testing."""
        return self.transcription_history
    
    def reset_history(self):
        """Reset transcription history."""
        self.transcription_history.clear()
        self.recognizer.reset()


# Factory function for easy mock creation
def create_vosk_mock(
    model_path: Optional[str] = None,
    sample_rate: int = 16000
) -> MockVoskTranscriber:
    """Create a mock Vosk transcriber with specified behavior."""
    return MockVoskTranscriber(model_path=model_path, sample_rate=sample_rate)


# Pytest fixtures
import pytest

@pytest.fixture
def vosk_mock():
    """Pytest fixture for Vosk mock."""
    return create_vosk_mock()


@pytest.fixture
def vosk_mock_spanish():
    """Pytest fixture for Spanish Vosk mock."""
    return create_vosk_mock(model_path="/mock/vosk/model-es")


@pytest.fixture
def vosk_mock_high_sample_rate():
    """Pytest fixture for Vosk mock with high sample rate."""
    return create_vosk_mock(sample_rate=44100)


@pytest.fixture
def mock_vosk_model():
    """Pytest fixture for mock Vosk model."""
    return MockVoskModel("/mock/vosk/model-en")


@pytest.fixture
def mock_vosk_recognizer(mock_vosk_model):
    """Pytest fixture for mock Vosk recognizer."""
    return MockVoskRecognizer(mock_vosk_model)