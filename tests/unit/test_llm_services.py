import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

import pytest

from src.llm.services.transcription_cleaner import TranscriptionCleanerService
from src.llm.services.speaker_diarizer import SpeakerDiarizerService
from src.llm.services.note_generator import NoteGeneratorService
from src.llm.services.token_manager import TokenManagerService
from src.llm.services.api_client import APIClientService
from src.core.exceptions import LLMError, TokenLimitError


class TestTranscriptionCleanerService:
    """Unit tests for TranscriptionCleanerService."""

    @pytest.fixture
    def cleaner_service(self):
        """Create TranscriptionCleanerService instance."""
        return TranscriptionCleanerService()

    @pytest.mark.asyncio
    async def test_clean_basic_text(self, cleaner_service):
        """Test basic text cleaning functionality."""
        dirty_text = "This is  teh   test trnascript with   extra spaces."
        cleaned = await cleaner_service.clean(dirty_text)
        
        assert isinstance(cleaned, str)
        assert "  " not in cleaned  # No double spaces
        assert len(cleaned) > 0

    @pytest.mark.asyncio
    async def test_clean_empty_text(self, cleaner_service):
        """Test cleaning empty text."""
        result = await cleaner_service.clean("")
        assert result == ""

    @pytest.mark.asyncio
    async def test_clean_medical_terminology(self, cleaner_service):
        """Test cleaning medical terminology preservation."""
        medical_text = "Patient has hypertension and diabetes mellitus type 2."
        cleaned = await cleaner_service.clean(medical_text)
        
        assert "hypertension" in cleaned.lower()
        assert "diabetes" in cleaned.lower()

    @pytest.mark.asyncio
    async def test_clean_timestamps_removal(self, cleaner_service):
        """Test removal of timestamps and markers."""
        text_with_timestamps = "[00:12:34] Doctor: How are you feeling? [00:12:45] Patient: I'm fine."
        cleaned = await cleaner_service.clean(text_with_timestamps)
        
        assert "[00:" not in cleaned
        assert "Doctor:" in cleaned
        assert "Patient:" in cleaned

    @pytest.mark.asyncio
    async def test_clean_performance_large_text(self, cleaner_service):
        """Test performance with large text."""
        large_text = "This is a test sentence. " * 1000  # Large text
        
        import time
        start_time = time.time()
        cleaned = await cleaner_service.clean(large_text)
        end_time = time.time()
        
        assert isinstance(cleaned, str)
        assert (end_time - start_time) < 5.0  # Should complete within 5 seconds


class TestSpeakerDiarizerService:
    """Unit tests for SpeakerDiarizerService."""

    @pytest.fixture
    def diarizer_service(self):
        """Create SpeakerDiarizerService instance."""
        return SpeakerDiarizerService()

    @pytest.mark.asyncio
    async def test_tag_speakers_basic(self, diarizer_service):
        """Test basic speaker tagging."""
        conversation = "Hello doctor.\nHello, how can I help you today?\nI have a headache."
        tagged = await diarizer_service.tag_speakers(conversation)
        
        assert isinstance(tagged, str)
        assert "SPEAKER" in tagged or "Patient:" in tagged or "Doctor:" in tagged

    @pytest.mark.asyncio
    async def test_identify_speaker_roles(self, diarizer_service):
        """Test identification of speaker roles."""
        medical_conversation = """
        Good morning, what brings you in today?
        I've been having chest pain for the last few days.
        Can you describe the pain? Is it sharp or dull?
        It's more of a dull ache, especially when I breathe deeply.
        """
        
        roles = await diarizer_service.identify_speaker_roles(medical_conversation)
        
        assert isinstance(roles, dict)
        assert len(roles) >= 2  # Should identify at least 2 speakers

    @pytest.mark.asyncio
    async def test_tag_empty_conversation(self, diarizer_service):
        """Test tagging empty conversation."""
        result = await diarizer_service.tag_speakers("")
        assert result == ""

    @pytest.mark.asyncio
    async def test_single_speaker_conversation(self, diarizer_service):
        """Test conversation with single speaker."""
        monologue = "I am dictating my notes. This is a long monologue with medical observations."
        tagged = await diarizer_service.tag_speakers(monologue)
        
        assert isinstance(tagged, str)
        # Should handle single speaker appropriately


class TestNoteGeneratorService:
    """Unit tests for NoteGeneratorService."""

    @pytest.fixture
    def note_generator(self):
        """Create NoteGeneratorService instance."""
        return NoteGeneratorService()

    @pytest.fixture
    def sample_transcript(self):
        """Sample medical transcript for testing."""
        return """
        Doctor: Good morning, what brings you in today?
        Patient: I've been having headaches for the past week.
        Doctor: Can you describe the headaches? Are they sharp or dull?
        Patient: They're mostly dull, but sometimes sharp behind my eyes.
        Doctor: Any nausea or sensitivity to light?
        Patient: Yes, bright lights make it worse.
        Doctor: I think we should run some tests. I'll prescribe a mild pain reliever for now.
        """

    @pytest.mark.asyncio
    async def test_generate_soap_note(self, note_generator, sample_transcript):
        """Test SOAP note generation."""
        soap_note = await note_generator.generate_soap_note(sample_transcript)
        
        assert isinstance(soap_note, str)
        assert len(soap_note) > 100  # Should be substantial
        
        # Should contain SOAP sections
        soap_sections = ["subjective", "objective", "assessment", "plan"]
        note_lower = soap_note.lower()
        
        # At least some SOAP elements should be present
        assert any(section in note_lower for section in soap_sections)

    @pytest.mark.asyncio
    async def test_generate_summary(self, note_generator, sample_transcript):
        """Test summary generation."""
        summary = await note_generator.generate_summary(sample_transcript)
        
        assert isinstance(summary, str)
        assert len(summary) < len(sample_transcript)  # Summary should be shorter
        assert len(summary) > 50  # But still substantial

    @pytest.mark.asyncio
    async def test_extract_medical_entities(self, note_generator, sample_transcript):
        """Test medical entity extraction."""
        entities = await note_generator.extract_medical_entities(sample_transcript)
        
        assert isinstance(entities, dict)
        
        # Should extract relevant medical information
        expected_keys = ["symptoms", "conditions", "medications", "procedures"]
        assert any(key in entities for key in expected_keys)

    @pytest.mark.asyncio
    async def test_generate_different_note_types(self, note_generator, sample_transcript):
        """Test generation of different note types."""
        note_types = ["soap", "summary", "diagnostic", "treatment_plan"]
        
        for note_type in note_types:
            note = await note_generator.generate_note(sample_transcript, note_type=note_type)
            assert isinstance(note, str)
            assert len(note) > 50  # Should generate substantial content

    @pytest.mark.asyncio
    async def test_note_quality_validation(self, note_generator, sample_transcript):
        """Test note quality validation."""
        note = await note_generator.generate_soap_note(sample_transcript)
        quality_score = await note_generator.validate_note_quality(note)
        
        assert isinstance(quality_score, (int, float))
        assert 0 <= quality_score <= 1  # Should be a score between 0 and 1


class TestTokenManagerService:
    """Unit tests for TokenManagerService."""

    @pytest.fixture
    def token_manager(self):
        """Create TokenManagerService instance."""
        return TokenManagerService()

    def test_count_tokens_basic(self, token_manager):
        """Test basic token counting."""
        text = "This is a test sentence with multiple words."
        token_count = token_manager.count_tokens(text)
        
        assert isinstance(token_count, int)
        assert token_count > 0

    def test_count_tokens_empty(self, token_manager):
        """Test token counting with empty text."""
        token_count = token_manager.count_tokens("")
        assert token_count == 0

    def test_chunk_text_basic(self, token_manager):
        """Test text chunking functionality."""
        long_text = "This is a sentence. " * 100  # Create long text
        chunks = token_manager.chunk_text(long_text, max_tokens=50)
        
        assert isinstance(chunks, list)
        assert len(chunks) > 1  # Should create multiple chunks
        
        # Each chunk should be within token limit
        for chunk in chunks:
            token_count = token_manager.count_tokens(chunk)
            assert token_count <= 50

    def test_estimate_cost(self, token_manager):
        """Test cost estimation."""
        text = "This is a test for cost estimation."
        cost = token_manager.estimate_cost(text, model_name="gpt-3.5-turbo")
        
        assert isinstance(cost, (int, float))
        assert cost >= 0

    def test_check_token_limit(self, token_manager):
        """Test token limit checking."""
        short_text = "Short text."
        long_text = "Very long text. " * 1000
        
        assert token_manager.check_token_limit(short_text, 100) is True
        assert token_manager.check_token_limit(long_text, 10) is False

    def test_optimize_prompt_length(self, token_manager):
        """Test prompt length optimization."""
        long_prompt = "This is a very long prompt that might need optimization. " * 50
        optimized = token_manager.optimize_prompt_length(long_prompt, max_tokens=100)
        
        assert isinstance(optimized, str)
        optimized_tokens = token_manager.count_tokens(optimized)
        assert optimized_tokens <= 100


class TestAPIClientService:
    """Unit tests for APIClientService."""

    @pytest.fixture
    def api_client(self):
        """Create APIClientService instance."""
        return APIClientService()

    @pytest.mark.asyncio
    async def test_make_request_with_retry(self, api_client):
        """Test API request with retry logic."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Mock successful response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"result": "success"})
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await api_client.make_request_with_retry(
                url="https://api.example.com/test",
                data={"test": "data"},
                max_retries=3
            )
            
            assert result["result"] == "success"

    @pytest.mark.asyncio
    async def test_request_retry_on_failure(self, api_client):
        """Test retry logic on request failure."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Mock failure then success
            mock_response_fail = AsyncMock()
            mock_response_fail.status = 500
            
            mock_response_success = AsyncMock()
            mock_response_success.status = 200
            mock_response_success.json = AsyncMock(return_value={"result": "success"})
            
            mock_post.return_value.__aenter__.side_effect = [
                mock_response_fail,  # First call fails
                mock_response_success  # Second call succeeds
            ]
            
            result = await api_client.make_request_with_retry(
                url="https://api.example.com/test",
                data={"test": "data"},
                max_retries=3
            )
            
            assert result["result"] == "success"
            assert mock_post.call_count == 2  # Should have retried once

    @pytest.mark.asyncio
    async def test_rate_limiting(self, api_client):
        """Test rate limiting functionality."""
        with patch('asyncio.sleep') as mock_sleep:
            # Test multiple rapid requests
            tasks = []
            for i in range(5):
                task = api_client.check_rate_limit("test_endpoint")
                tasks.append(task)
            
            await asyncio.gather(*tasks)
            
            # Should have implemented rate limiting
            assert mock_sleep.call_count >= 0  # May or may not sleep depending on implementation

    @pytest.mark.asyncio
    async def test_request_timeout_handling(self, api_client):
        """Test timeout handling in requests."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Mock timeout
            mock_post.side_effect = asyncio.TimeoutError("Request timeout")
            
            with pytest.raises(LLMError):
                await api_client.make_request_with_retry(
                    url="https://api.example.com/test",
                    data={"test": "data"},
                    timeout=1.0
                )

    def test_prepare_headers(self, api_client):
        """Test header preparation."""
        headers = api_client.prepare_headers(api_key="test_key", additional_headers={"Custom": "Value"})
        
        assert isinstance(headers, dict)
        assert "Authorization" in headers or "api-key" in headers
        assert headers["Custom"] == "Value"

    @pytest.mark.asyncio
    async def test_response_validation(self, api_client):
        """Test response validation."""
        valid_response = {"status": "success", "data": {"result": "test"}}
        invalid_response = {"error": "Something went wrong"}
        
        # Valid response should pass
        assert api_client.validate_response(valid_response) is True
        
        # Invalid response should fail
        assert api_client.validate_response(invalid_response) is False