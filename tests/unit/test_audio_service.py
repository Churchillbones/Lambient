import asyncio
import io
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import wave
import numpy as np

from src.core.services.audio_service import AudioService
from src.core.interfaces.audio_service import IAudioService
from src.core.exceptions import AudioProcessingError


class TestAudioService:
    """Comprehensive unit tests for AudioService."""

    @pytest.fixture
    def audio_service(self):
        """Create AudioService instance for testing."""
        return AudioService()

    @pytest.fixture
    def sample_wav_data(self):
        """Create sample WAV audio data for testing."""
        sample_rate = 16000
        duration = 1.0  # 1 second
        frequency = 440  # A4 note
        
        # Generate sine wave
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio_data = np.sin(frequency * 2 * np.pi * t) * 0.5
        
        # Convert to 16-bit PCM
        audio_data = (audio_data * 32767).astype(np.int16)
        
        # Create WAV file in memory
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        wav_buffer.seek(0)
        return wav_buffer.getvalue()

    @pytest.fixture
    def temp_audio_file(self, sample_wav_data):
        """Create temporary audio file for testing."""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(sample_wav_data)
            temp_file.flush()
            yield Path(temp_file.name)
        
        # Cleanup
        Path(temp_file.name).unlink(missing_ok=True)

    def test_audio_service_implements_interface(self, audio_service):
        """Test that AudioService implements IAudioService interface."""
        assert isinstance(audio_service, IAudioService)

    @pytest.mark.asyncio
    async def test_validate_audio_file_valid_wav(self, audio_service, temp_audio_file):
        """Test validation of valid WAV file."""
        result = await audio_service.validate_audio_file(str(temp_audio_file))
        
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_audio_file_nonexistent(self, audio_service):
        """Test validation of non-existent file."""
        with pytest.raises(AudioProcessingError):
            await audio_service.validate_audio_file("/nonexistent/file.wav")

    @pytest.mark.asyncio
    async def test_validate_audio_file_invalid_format(self, audio_service):
        """Test validation of invalid audio format."""
        with tempfile.NamedTemporaryFile(suffix='.txt', mode='w') as temp_file:
            temp_file.write("This is not audio data")
            temp_file.flush()
            
            with pytest.raises(AudioProcessingError):
                await audio_service.validate_audio_file(temp_file.name)

    @pytest.mark.asyncio
    async def test_get_audio_metadata(self, audio_service, temp_audio_file):
        """Test audio metadata extraction."""
        metadata = await audio_service.get_audio_metadata(str(temp_audio_file))
        
        assert metadata['duration'] > 0
        assert metadata['sample_rate'] == 16000
        assert metadata['channels'] == 1
        assert metadata['format'] == 'wav'

    @pytest.mark.asyncio
    async def test_convert_to_wav_already_wav(self, audio_service, temp_audio_file):
        """Test conversion when file is already WAV format."""
        result_path = await audio_service.convert_to_wav(str(temp_audio_file))
        
        # Should return the same file path since it's already WAV
        assert Path(result_path) == temp_audio_file

    @pytest.mark.asyncio
    async def test_normalize_audio_levels(self, audio_service, temp_audio_file):
        """Test audio level normalization."""
        normalized_path = await audio_service.normalize_audio_levels(str(temp_audio_file))
        
        assert Path(normalized_path).exists()
        assert normalized_path.endswith('.wav')
        
        # Cleanup
        if normalized_path != str(temp_audio_file):
            Path(normalized_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_reduce_noise_basic(self, audio_service, temp_audio_file):
        """Test basic noise reduction functionality."""
        cleaned_path = await audio_service.reduce_noise(str(temp_audio_file))
        
        assert Path(cleaned_path).exists()
        assert cleaned_path.endswith('.wav')
        
        # Cleanup
        if cleaned_path != str(temp_audio_file):
            Path(cleaned_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_process_audio_chunk_streaming(self, audio_service, sample_wav_data):
        """Test processing audio chunks for streaming."""
        chunk_result = await audio_service.process_audio_chunk(sample_wav_data)
        
        assert isinstance(chunk_result, bytes)
        assert len(chunk_result) > 0

    @pytest.mark.asyncio
    async def test_get_supported_formats(self, audio_service):
        """Test getting supported audio formats."""
        formats = await audio_service.get_supported_formats()
        
        assert isinstance(formats, list)
        assert 'wav' in formats
        assert 'mp3' in formats or 'flac' in formats

    @pytest.mark.asyncio
    async def test_estimate_processing_time(self, audio_service, temp_audio_file):
        """Test processing time estimation."""
        estimated_time = await audio_service.estimate_processing_time(str(temp_audio_file))
        
        assert isinstance(estimated_time, (int, float))
        assert estimated_time > 0

    @pytest.mark.asyncio
    async def test_audio_service_error_handling(self, audio_service):
        """Test proper error handling in audio service."""
        # Test with empty string
        with pytest.raises(AudioProcessingError):
            await audio_service.validate_audio_file("")
        
        # Test with None
        with pytest.raises((AudioProcessingError, TypeError)):
            await audio_service.validate_audio_file(None)

    @pytest.mark.asyncio
    async def test_concurrent_audio_processing(self, audio_service, temp_audio_file):
        """Test concurrent audio processing operations."""
        # Run multiple operations concurrently
        tasks = [
            audio_service.validate_audio_file(str(temp_audio_file)),
            audio_service.get_audio_metadata(str(temp_audio_file)),
            audio_service.estimate_processing_time(str(temp_audio_file))
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert results[0] is True  # validation
        assert isinstance(results[1], dict)  # metadata
        assert isinstance(results[2], (int, float))  # processing time

    def test_audio_service_cleanup_on_error(self, audio_service):
        """Test that resources are properly cleaned up on errors."""
        # This would test internal cleanup mechanisms
        # Implementation depends on specific cleanup logic in AudioService
        pass

    @pytest.mark.asyncio
    async def test_memory_usage_large_files(self, audio_service):
        """Test memory usage with large audio files."""
        # Create a larger audio file for memory testing
        large_audio_data = np.random.randint(-32767, 32767, 16000 * 30, dtype=np.int16)  # 30 seconds
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(16000)
                wav_file.writeframes(large_audio_data.tobytes())
            
            temp_file.write(wav_buffer.getvalue())
            temp_file.flush()
            
            try:
                # This should not cause memory issues
                metadata = await audio_service.get_audio_metadata(temp_file.name)
                assert metadata['duration'] > 25  # Should be around 30 seconds
            finally:
                Path(temp_file.name).unlink(missing_ok=True)