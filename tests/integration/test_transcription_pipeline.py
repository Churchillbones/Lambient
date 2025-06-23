"""Integration tests for complete transcription pipeline."""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.core.bootstrap import bootstrap_container
from src.core.interfaces.audio_service import IAudioService
from src.core.interfaces.streaming_service import IStreamingService
from src.llm.pipeline.orchestrator import LLMOrchestrator
from src.llm.services.transcription_cleaner import TranscriptionCleanerService
from src.llm.services.note_generator import NoteGeneratorService
from tests.mocks.azure_openai_mock import create_azure_openai_mock
from tests.mocks.azure_speech_mock import create_azure_speech_mock
from tests.mocks.vosk_mock import create_vosk_mock


class TestTranscriptionPipelineIntegration:
    """Integration tests for the complete transcription pipeline."""
    
    @pytest.fixture
    async def container(self):
        """Set up dependency injection container."""
        container = bootstrap_container()
        return container
    
    @pytest.fixture
    def sample_audio_file(self):
        """Create sample audio file for testing."""
        # Create a temporary WAV file with mock content
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            # Write minimal WAV header
            wav_header = b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\x08\x00\x00'
            # Add some mock audio data
            audio_data = b'\x00\x00' * 4000  # Silence
            temp_file.write(wav_header + audio_data)
            temp_file.flush()
            
            yield Path(temp_file.name)
        
        # Cleanup
        Path(temp_file.name).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_end_to_end_transcription_vosk_to_note(
        self, 
        container,
        sample_audio_file
    ):
        """Test complete pipeline: Audio → Vosk Transcription → LLM Note Generation."""
        
        # Mock external services
        with patch('src.asr.transcribers.vosk.VoskTranscriber') as mock_vosk_class:
            with patch('src.core.providers.azure_openai_provider.AzureOpenAIProvider') as mock_llm_class:
                
                # Set up mocks
                mock_vosk = create_vosk_mock()
                mock_llm = create_azure_openai_mock()
                mock_vosk_class.return_value = mock_vosk
                mock_llm_class.return_value = mock_llm
                
                # Get services from container
                audio_service = container.resolve(IAudioService)
                
                # Step 1: Validate audio file
                is_valid = await audio_service.validate_audio_file(str(sample_audio_file))
                assert is_valid is True
                
                # Step 2: Get audio metadata
                metadata = await audio_service.get_audio_metadata(str(sample_audio_file))
                assert metadata['duration'] > 0
                assert metadata['format'] == 'wav'
                
                # Step 3: Transcribe audio
                transcription = await mock_vosk.transcribe(str(sample_audio_file))
                assert isinstance(transcription, str)
                assert len(transcription) > 0
                
                # Step 4: Clean transcription
                cleaner = TranscriptionCleanerService()
                cleaned_transcription = await cleaner.clean(transcription)
                assert isinstance(cleaned_transcription, str)
                
                # Step 5: Generate medical note
                note_generator = NoteGeneratorService()
                with patch.object(note_generator, '_llm_provider', mock_llm):
                    medical_note = await note_generator.generate_soap_note(cleaned_transcription)
                    assert isinstance(medical_note, str)
                    assert len(medical_note) > 50  # Should be substantial
                
                # Verify the complete workflow
                assert transcription != cleaned_transcription or len(transcription) > 10
                assert "soap" in medical_note.lower() or "subjective" in medical_note.lower()
    
    @pytest.mark.asyncio
    async def test_end_to_end_transcription_azure_to_note(
        self,
        container,
        sample_audio_file
    ):
        """Test complete pipeline: Audio → Azure Speech → LLM Note Generation."""
        
        with patch('src.asr.transcribers.azure_speech.AzureSpeechTranscriber') as mock_azure_class:
            with patch('src.core.providers.azure_openai_provider.AzureOpenAIProvider') as mock_llm_class:
                
                # Set up mocks
                mock_azure = create_azure_speech_mock()
                mock_llm = create_azure_openai_mock()
                mock_azure_class.return_value = mock_azure
                mock_llm_class.return_value = mock_llm
                
                # Get audio service
                audio_service = container.resolve(IAudioService)
                
                # Process audio through Azure Speech
                transcription = await mock_azure.transcribe(str(sample_audio_file))
                assert isinstance(transcription, str)
                assert len(transcription) > 0
                
                # Generate note with orchestrator
                orchestrator = LLMOrchestrator()
                with patch.object(orchestrator, '_get_llm_provider', return_value=mock_llm):
                    note = await orchestrator.process_transcription(
                        transcription=transcription,
                        note_type="soap",
                        patient_context={}
                    )
                    
                    assert isinstance(note, dict)
                    assert "content" in note
                    assert "metadata" in note
                    assert len(note["content"]) > 50
    
    @pytest.mark.asyncio
    async def test_pipeline_with_multiple_transcribers(
        self,
        container,
        sample_audio_file
    ):
        """Test pipeline using multiple transcribers for comparison."""
        
        with patch('src.asr.transcribers.vosk.VoskTranscriber') as mock_vosk_class:
            with patch('src.asr.transcribers.azure_speech.AzureSpeechTranscriber') as mock_azure_class:
                
                # Set up mocks
                mock_vosk = create_vosk_mock()
                mock_azure = create_azure_speech_mock()
                mock_vosk_class.return_value = mock_vosk
                mock_azure_class.return_value = mock_azure
                
                # Transcribe with both services
                vosk_transcription = await mock_vosk.transcribe(str(sample_audio_file))
                azure_transcription = await mock_azure.transcribe(str(sample_audio_file))
                
                # Both should return valid transcriptions
                assert isinstance(vosk_transcription, str)
                assert isinstance(azure_transcription, str)
                assert len(vosk_transcription) > 0
                assert len(azure_transcription) > 0
                
                # Transcriptions may differ but should be related
                assert vosk_transcription != azure_transcription  # Different mock responses
    
    @pytest.mark.asyncio
    async def test_pipeline_error_handling_and_recovery(
        self,
        container,
        sample_audio_file
    ):
        """Test pipeline error handling and recovery mechanisms."""
        
        with patch('src.asr.transcribers.vosk.VoskTranscriber') as mock_vosk_class:
            with patch('src.core.providers.azure_openai_provider.AzureOpenAIProvider') as mock_llm_class:
                
                # Create mocks that fail after certain calls
                mock_vosk = create_vosk_mock()
                mock_llm = create_azure_openai_mock(fail_after=1)  # Fail after 1 call
                
                mock_vosk_class.return_value = mock_vosk
                mock_llm_class.return_value = mock_llm
                
                # First transcription should succeed
                transcription = await mock_vosk.transcribe(str(sample_audio_file))
                assert isinstance(transcription, str)
                
                # First LLM call should succeed
                note_generator = NoteGeneratorService()
                with patch.object(note_generator, '_llm_provider', mock_llm):
                    first_note = await note_generator.generate_summary(transcription)
                    assert isinstance(first_note, str)
                    
                    # Second LLM call should fail
                    with pytest.raises(Exception):
                        await note_generator.generate_soap_note(transcription)
    
    @pytest.mark.asyncio
    async def test_pipeline_performance_under_load(
        self,
        container,
        sample_audio_file
    ):
        """Test pipeline performance with multiple concurrent requests."""
        
        with patch('src.asr.transcribers.vosk.VoskTranscriber') as mock_vosk_class:
            with patch('src.core.providers.azure_openai_provider.AzureOpenAIProvider') as mock_llm_class:
                
                # Set up mocks with artificial delays
                mock_vosk = create_vosk_mock()
                mock_llm = create_azure_openai_mock(delay=0.1)  # 100ms delay
                
                mock_vosk_class.return_value = mock_vosk
                mock_llm_class.return_value = mock_llm
                
                # Create multiple concurrent transcription tasks
                async def transcribe_and_generate_note():
                    transcription = await mock_vosk.transcribe(str(sample_audio_file))
                    
                    note_generator = NoteGeneratorService()
                    with patch.object(note_generator, '_llm_provider', mock_llm):
                        note = await note_generator.generate_summary(transcription)
                        return note
                
                # Run 5 concurrent tasks
                tasks = [transcribe_and_generate_note() for _ in range(5)]
                
                import time
                start_time = time.time()
                results = await asyncio.gather(*tasks)
                end_time = time.time()
                
                # Verify all tasks completed
                assert len(results) == 5
                for result in results:
                    assert isinstance(result, str)
                    assert len(result) > 0
                
                # Should complete in reasonable time (< 5 seconds for 5 concurrent tasks)
                total_time = end_time - start_time
                assert total_time < 5.0
    
    @pytest.mark.asyncio
    async def test_pipeline_with_different_audio_formats(
        self,
        container
    ):
        """Test pipeline with different audio formats."""
        
        # Create different format files
        formats = [
            ('.wav', b'RIFF\x24\x08\x00\x00WAVEfmt '),
            ('.mp3', b'ID3\x03\x00\x00\x00'),  # MP3 header
            ('.flac', b'fLaC\x00\x00\x00"')   # FLAC header
        ]
        
        with patch('src.asr.transcribers.vosk.VoskTranscriber') as mock_vosk_class:
            mock_vosk = create_vosk_mock()
            mock_vosk_class.return_value = mock_vosk
            
            audio_service = container.resolve(IAudioService)
            
            for extension, header in formats:
                with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as temp_file:
                    # Write format-specific header + mock data
                    temp_file.write(header + b'\x00' * 1000)
                    temp_file.flush()
                    
                    try:
                        # Test audio validation
                        if extension == '.wav':  # Only WAV should validate without conversion
                            is_valid = await audio_service.validate_audio_file(temp_file.name)
                            assert is_valid is True
                        
                        # Test transcription (should work for all formats after conversion)
                        transcription = await mock_vosk.transcribe(temp_file.name)
                        assert isinstance(transcription, str)
                        
                    finally:
                        Path(temp_file.name).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_pipeline_context_preservation(
        self,
        container,
        sample_audio_file
    ):
        """Test that context is preserved through the pipeline."""
        
        with patch('src.asr.transcribers.vosk.VoskTranscriber') as mock_vosk_class:
            with patch('src.core.providers.azure_openai_provider.AzureOpenAIProvider') as mock_llm_class:
                
                mock_vosk = create_vosk_mock()
                mock_llm = create_azure_openai_mock()
                mock_vosk_class.return_value = mock_vosk
                mock_llm_class.return_value = mock_llm
                
                # Create context with patient information
                patient_context = {
                    "patient_id": "TEST_001",
                    "encounter_id": "ENC_123",
                    "provider": "Dr. Test",
                    "specialty": "Internal Medicine"
                }
                
                # Process through orchestrator with context
                orchestrator = LLMOrchestrator()
                
                # First get transcription
                transcription = await mock_vosk.transcribe(str(sample_audio_file))
                
                # Process with context
                with patch.object(orchestrator, '_get_llm_provider', return_value=mock_llm):
                    result = await orchestrator.process_transcription(
                        transcription=transcription,
                        note_type="soap",
                        patient_context=patient_context
                    )
                    
                    # Verify context is preserved in metadata
                    assert "metadata" in result
                    assert result["metadata"]["patient_id"] == "TEST_001"
                    assert result["metadata"]["encounter_id"] == "ENC_123"
                    assert result["metadata"]["provider"] == "Dr. Test"
    
    @pytest.mark.asyncio
    async def test_pipeline_quality_metrics(
        self,
        container,
        sample_audio_file
    ):
        """Test quality metrics collection throughout the pipeline."""
        
        with patch('src.asr.transcribers.vosk.VoskTranscriber') as mock_vosk_class:
            with patch('src.core.providers.azure_openai_provider.AzureOpenAIProvider') as mock_llm_class:
                
                mock_vosk = create_vosk_mock()
                mock_llm = create_azure_openai_mock()
                mock_vosk_class.return_value = mock_vosk
                mock_llm_class.return_value = mock_llm
                
                # Track metrics through pipeline
                metrics = {}
                
                # Audio processing metrics
                audio_service = container.resolve(IAudioService)
                
                import time
                start_time = time.time()
                metadata = await audio_service.get_audio_metadata(str(sample_audio_file))
                audio_time = time.time() - start_time
                
                metrics["audio_processing_time"] = audio_time
                metrics["audio_duration"] = metadata["duration"]
                
                # Transcription metrics
                start_time = time.time()
                transcription = await mock_vosk.transcribe(str(sample_audio_file))
                transcription_time = time.time() - start_time
                
                metrics["transcription_time"] = transcription_time
                metrics["transcription_length"] = len(transcription)
                
                # Note generation metrics
                note_generator = NoteGeneratorService()
                with patch.object(note_generator, '_llm_provider', mock_llm):
                    start_time = time.time()
                    note = await note_generator.generate_soap_note(transcription)
                    note_generation_time = time.time() - start_time
                    
                    metrics["note_generation_time"] = note_generation_time
                    metrics["note_length"] = len(note)
                
                # Verify metrics are reasonable
                assert metrics["audio_processing_time"] < 1.0  # Should be fast
                assert metrics["transcription_time"] < 2.0  # Should be reasonable
                assert metrics["note_generation_time"] < 3.0  # Should complete
                assert metrics["transcription_length"] > 0
                assert metrics["note_length"] > metrics["transcription_length"]  # Note should be longer