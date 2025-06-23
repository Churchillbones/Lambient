"""Mock Azure Speech service for testing."""

import asyncio
import json
import random
from typing import Dict, Any, List, Optional, AsyncGenerator
from unittest.mock import AsyncMock
import io


class MockAzureSpeechResult:
    """Mock result object for Azure Speech recognition."""
    
    def __init__(self, text: str, confidence: float = 0.95, reason: str = "RecognizedSpeech"):
        self.text = text
        self.reason = reason
        self.confidence = confidence
        self.duration = random.uniform(1.0, 5.0)  # Mock duration
        self.offset = random.randint(1000, 10000)  # Mock offset
    
    @property
    def json(self) -> str:
        """Return JSON representation."""
        return json.dumps({
            "RecognitionStatus": "Success",
            "DisplayText": self.text,
            "Offset": self.offset,
            "Duration": int(self.duration * 10000000),  # Convert to ticks
            "NBest": [
                {
                    "Confidence": self.confidence,
                    "Lexical": self.text.lower(),
                    "ITN": self.text,
                    "MaskedITN": self.text,
                    "Display": self.text
                }
            ]
        })


class MockAzureSpeechRecognizer:
    """Mock Azure Speech recognizer for testing."""
    
    def __init__(self, fail_probability: float = 0.0, delay: float = 0.1):
        """
        Initialize mock recognizer.
        
        Args:
            fail_probability: Probability of recognition failure (0.0 to 1.0)
            delay: Artificial delay to simulate processing time
        """
        self.fail_probability = fail_probability
        self.delay = delay
        self.recognition_count = 0
        self.recognition_history: List[Dict[str, Any]] = []
        self._is_recognizing = False
    
    async def recognize_once_async(self, audio_data: bytes) -> MockAzureSpeechResult:
        """Mock single recognition from audio data."""
        await asyncio.sleep(self.delay)
        
        self.recognition_count += 1
        
        # Simulate random failure
        if random.random() < self.fail_probability:
            raise Exception("Mock Azure Speech recognition error")
        
        # Generate mock transcription based on audio length
        audio_length = len(audio_data)
        mock_text = self._generate_mock_transcription(audio_length)
        
        # Record recognition attempt
        self.recognition_history.append({
            "audio_length": audio_length,
            "result": mock_text,
            "timestamp": self.recognition_count
        })
        
        return MockAzureSpeechResult(mock_text)
    
    async def start_continuous_recognition(self) -> None:
        """Start continuous recognition (mock)."""
        self._is_recognizing = True
    
    async def stop_continuous_recognition(self) -> None:
        """Stop continuous recognition (mock)."""
        self._is_recognizing = False
    
    def _generate_mock_transcription(self, audio_length: int) -> str:
        """Generate mock transcription based on audio length."""
        # Longer audio = more text
        base_phrases = [
            "The patient reports feeling unwell",
            "Doctor examines the patient carefully",
            "Vital signs appear to be stable",
            "Patient describes symptoms in detail",
            "Medical history is reviewed thoroughly",
            "Treatment plan is discussed with patient",
            "Follow-up appointment is scheduled"
        ]
        
        # Determine number of phrases based on audio length
        num_phrases = max(1, audio_length // 1000)  # Rough approximation
        num_phrases = min(num_phrases, len(base_phrases))
        
        selected_phrases = random.sample(base_phrases, num_phrases)
        return ". ".join(selected_phrases) + "."
    
    @property
    def is_recognizing(self) -> bool:
        """Check if recognizer is currently recognizing."""
        return self._is_recognizing


class MockAzureSpeechTranscriber:
    """Mock Azure Speech transcriber that mimics the real transcriber interface."""
    
    def __init__(self, recognizer: Optional[MockAzureSpeechRecognizer] = None):
        self.recognizer = recognizer or MockAzureSpeechRecognizer()
        self._language = "en-US"
        self._model_name = "latest"
    
    async def transcribe(self, audio_file_path: str) -> str:
        """Transcribe audio file (mock)."""
        # Simulate reading audio file
        try:
            with open(audio_file_path, 'rb') as f:
                audio_data = f.read()
        except FileNotFoundError:
            # For testing with non-existent files
            audio_data = b"mock_audio_data" * 100
        
        result = await self.recognizer.recognize_once_async(audio_data)
        return result.text
    
    async def transcribe_stream(self, audio_stream: io.BytesIO) -> AsyncGenerator[str, None]:
        """Transcribe audio stream with partial results."""
        audio_data = audio_stream.read()
        chunk_size = len(audio_data) // 5  # Simulate 5 chunks
        
        if chunk_size == 0:
            chunk_size = len(audio_data)
        
        full_text = ""
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i + chunk_size]
            
            # Generate partial result
            result = await self.recognizer.recognize_once_async(chunk)
            partial_text = result.text
            full_text += " " + partial_text
            
            # Yield partial result
            yield {
                "partial": True,
                "text": partial_text,
                "confidence": result.confidence,
                "is_final": i + chunk_size >= len(audio_data)
            }
            
            await asyncio.sleep(0.1)  # Simulate streaming delay
    
    async def start_streaming(self) -> None:
        """Start streaming recognition."""
        await self.recognizer.start_continuous_recognition()
    
    async def stop_streaming(self) -> None:
        """Stop streaming recognition."""
        await self.recognizer.stop_continuous_recognition()
    
    def get_recognition_history(self) -> List[Dict[str, Any]]:
        """Get recognition history for testing."""
        return self.recognizer.recognition_history
    
    def reset_history(self):
        """Reset recognition history."""
        self.recognizer.recognition_history.clear()
        self.recognizer.recognition_count = 0


class MockAzureSpeechConfig:
    """Mock Azure Speech configuration."""
    
    def __init__(self, subscription_key: str, region: str):
        self.subscription_key = subscription_key
        self.region = region
        self.speech_recognition_language = "en-US"
        self.endpoint_id = None
    
    @classmethod
    def from_subscription(cls, subscription_key: str, region: str):
        """Create config from subscription."""
        return cls(subscription_key, region)


# Factory functions for easy mock creation
def create_azure_speech_mock(
    fail_probability: float = 0.0,
    delay: float = 0.1
) -> MockAzureSpeechTranscriber:
    """Create a mock Azure Speech transcriber with specified behavior."""
    recognizer = MockAzureSpeechRecognizer(fail_probability=fail_probability, delay=delay)
    return MockAzureSpeechTranscriber(recognizer)


# Pytest fixtures
import pytest

@pytest.fixture
def azure_speech_mock():
    """Pytest fixture for Azure Speech mock."""
    return create_azure_speech_mock()


@pytest.fixture
def azure_speech_mock_with_failures():
    """Pytest fixture for Azure Speech mock with 20% failure rate."""
    return create_azure_speech_mock(fail_probability=0.2)


@pytest.fixture
def azure_speech_mock_slow():
    """Pytest fixture for Azure Speech mock with artificial delay."""
    return create_azure_speech_mock(delay=1.0)


@pytest.fixture
def azure_speech_config_mock():
    """Pytest fixture for Azure Speech config mock."""
    return MockAzureSpeechConfig("mock_key", "mock_region")