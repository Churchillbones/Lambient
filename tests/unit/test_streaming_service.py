import asyncio
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

import pytest
import websockets

from src.core.services.streaming_service import StreamingService
from src.core.interfaces.streaming_service import IStreamingService
from src.core.exceptions import StreamingError


class TestStreamingService:
    """Comprehensive unit tests for StreamingService."""

    @pytest.fixture
    def streaming_service(self):
        """Create StreamingService instance for testing."""
        return StreamingService()

    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket for testing."""
        mock_ws = MagicMock()
        mock_ws.send = AsyncMock()
        mock_ws.recv = AsyncMock()
        mock_ws.close = AsyncMock()
        mock_ws.closed = False
        return mock_ws

    @pytest.fixture
    def sample_session_id(self):
        """Create sample session ID for testing."""
        return str(uuid.uuid4())

    @pytest.fixture
    def sample_audio_data(self):
        """Create sample audio data for testing."""
        return b"fake_audio_data_for_testing" * 100  # Simulate audio chunk

    def test_streaming_service_implements_interface(self, streaming_service):
        """Test that StreamingService implements IStreamingService interface."""
        assert isinstance(streaming_service, IStreamingService)

    @pytest.mark.asyncio
    async def test_create_session(self, streaming_service, mock_websocket):
        """Test session creation."""
        session_id = await streaming_service.create_session(
            websocket=mock_websocket,
            transcriber_type="vosk",
            config={"language": "en"}
        )
        
        assert isinstance(session_id, str)
        assert uuid.UUID(session_id)  # Should be valid UUID
        
        # Session should be tracked
        sessions = await streaming_service.get_active_sessions()
        assert session_id in sessions

    @pytest.mark.asyncio
    async def test_create_session_invalid_transcriber(self, streaming_service, mock_websocket):
        """Test session creation with invalid transcriber type."""
        with pytest.raises(StreamingError):
            await streaming_service.create_session(
                websocket=mock_websocket,
                transcriber_type="invalid_transcriber",
                config={}
            )

    @pytest.mark.asyncio
    async def test_process_audio_chunk(self, streaming_service, mock_websocket, sample_audio_data):
        """Test audio chunk processing."""
        # Create session first
        session_id = await streaming_service.create_session(
            websocket=mock_websocket,
            transcriber_type="vosk",
            config={"language": "en"}
        )
        
        # Process audio chunk
        result = await streaming_service.process_audio_chunk(session_id, sample_audio_data)
        
        assert isinstance(result, dict)
        assert "partial_result" in result or "final_result" in result

    @pytest.mark.asyncio
    async def test_process_audio_chunk_invalid_session(self, streaming_service, sample_audio_data):
        """Test processing audio chunk with invalid session ID."""
        invalid_session_id = str(uuid.uuid4())
        
        with pytest.raises(StreamingError):
            await streaming_service.process_audio_chunk(invalid_session_id, sample_audio_data)

    @pytest.mark.asyncio
    async def test_send_result(self, streaming_service, mock_websocket):
        """Test sending results to WebSocket."""
        session_id = await streaming_service.create_session(
            websocket=mock_websocket,
            transcriber_type="vosk",
            config={}
        )
        
        result = {
            "type": "partial",
            "text": "Hello world",
            "confidence": 0.95,
            "timestamp": 1234567890
        }
        
        await streaming_service.send_result(session_id, result)
        
        # Verify WebSocket send was called
        mock_websocket.send.assert_called_once()
        sent_data = mock_websocket.send.call_args[0][0]
        parsed_data = json.loads(sent_data)
        
        assert parsed_data["session_id"] == session_id
        assert parsed_data["result"] == result

    @pytest.mark.asyncio
    async def test_close_session(self, streaming_service, mock_websocket):
        """Test session closure."""
        session_id = await streaming_service.create_session(
            websocket=mock_websocket,
            transcriber_type="vosk",
            config={}
        )
        
        # Verify session exists
        sessions = await streaming_service.get_active_sessions()
        assert session_id in sessions
        
        # Close session
        await streaming_service.close_session(session_id)
        
        # Verify session is removed
        sessions = await streaming_service.get_active_sessions()
        assert session_id not in sessions

    @pytest.mark.asyncio
    async def test_close_nonexistent_session(self, streaming_service):
        """Test closing non-existent session."""
        invalid_session_id = str(uuid.uuid4())
        
        # Should not raise error for non-existent session
        await streaming_service.close_session(invalid_session_id)

    @pytest.mark.asyncio
    async def test_get_session_info(self, streaming_service, mock_websocket):
        """Test getting session information."""
        session_id = await streaming_service.create_session(
            websocket=mock_websocket,
            transcriber_type="vosk",
            config={"language": "en", "model": "vosk-model-en-us-0.22"}
        )
        
        session_info = await streaming_service.get_session_info(session_id)
        
        assert session_info["session_id"] == session_id
        assert session_info["transcriber_type"] == "vosk"
        assert session_info["config"]["language"] == "en"
        assert "created_at" in session_info
        assert "status" in session_info

    @pytest.mark.asyncio
    async def test_get_session_stats(self, streaming_service, mock_websocket, sample_audio_data):
        """Test getting session statistics."""
        session_id = await streaming_service.create_session(
            websocket=mock_websocket,
            transcriber_type="vosk",
            config={}
        )
        
        # Process some audio to generate stats
        await streaming_service.process_audio_chunk(session_id, sample_audio_data)
        await streaming_service.process_audio_chunk(session_id, sample_audio_data)
        
        stats = await streaming_service.get_session_stats(session_id)
        
        assert "chunks_processed" in stats
        assert "total_audio_duration" in stats
        assert "average_processing_time" in stats
        assert stats["chunks_processed"] >= 2

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, streaming_service, mock_websocket):
        """Test cleanup of expired sessions."""
        # Create a session
        session_id = await streaming_service.create_session(
            websocket=mock_websocket,
            transcriber_type="vosk",
            config={}
        )
        
        # Mock the session as expired
        with patch.object(streaming_service, '_is_session_expired', return_value=True):
            await streaming_service.cleanup_expired_sessions()
        
        # Session should be removed
        sessions = await streaming_service.get_active_sessions()
        assert session_id not in sessions

    @pytest.mark.asyncio
    async def test_concurrent_sessions(self, streaming_service):
        """Test handling multiple concurrent sessions."""
        mock_ws1 = MagicMock()
        mock_ws1.send = AsyncMock()
        mock_ws2 = MagicMock()
        mock_ws2.send = AsyncMock()
        
        # Create multiple sessions concurrently
        session1_task = streaming_service.create_session(mock_ws1, "vosk", {"language": "en"})
        session2_task = streaming_service.create_session(mock_ws2, "whisper", {"language": "es"})
        
        session1_id, session2_id = await asyncio.gather(session1_task, session2_task)
        
        # Both sessions should exist
        sessions = await streaming_service.get_active_sessions()
        assert session1_id in sessions
        assert session2_id in sessions
        
        # Sessions should have different configurations
        info1 = await streaming_service.get_session_info(session1_id)
        info2 = await streaming_service.get_session_info(session2_id)
        
        assert info1["transcriber_type"] == "vosk"
        assert info2["transcriber_type"] == "whisper"
        assert info1["config"]["language"] == "en"
        assert info2["config"]["language"] == "es"

    @pytest.mark.asyncio
    async def test_websocket_error_handling(self, streaming_service):
        """Test handling WebSocket errors."""
        mock_ws = MagicMock()
        mock_ws.send = AsyncMock(side_effect=websockets.exceptions.ConnectionClosed(None, None))
        
        session_id = await streaming_service.create_session(
            websocket=mock_ws,
            transcriber_type="vosk",
            config={}
        )
        
        # Sending result should handle WebSocket error gracefully
        result = {"type": "partial", "text": "test"}
        
        # Should not raise exception
        await streaming_service.send_result(session_id, result)
        
        # Session should be marked as disconnected or removed
        session_info = await streaming_service.get_session_info(session_id)
        assert session_info["status"] in ["disconnected", "error"]

    @pytest.mark.asyncio
    async def test_resource_monitoring(self, streaming_service, mock_websocket):
        """Test resource monitoring functionality."""
        session_id = await streaming_service.create_session(
            websocket=mock_websocket,
            transcriber_type="vosk",
            config={}
        )
        
        # Get resource usage
        resources = await streaming_service.get_resource_usage(session_id)
        
        assert "memory_usage" in resources
        assert "cpu_usage" in resources
        assert "audio_buffer_size" in resources
        assert isinstance(resources["memory_usage"], (int, float))

    @pytest.mark.asyncio
    async def test_session_timeout_handling(self, streaming_service, mock_websocket):
        """Test session timeout handling."""
        # Create session with short timeout
        session_id = await streaming_service.create_session(
            websocket=mock_websocket,
            transcriber_type="vosk",
            config={"session_timeout": 0.1}  # 100ms timeout
        )
        
        # Wait longer than timeout
        await asyncio.sleep(0.2)
        
        # Process timeout checks
        await streaming_service.cleanup_expired_sessions()
        
        # Session should be expired and removed
        sessions = await streaming_service.get_active_sessions()
        assert session_id not in sessions

    @pytest.mark.asyncio
    async def test_audio_buffer_management(self, streaming_service, mock_websocket, sample_audio_data):
        """Test audio buffer management."""
        session_id = await streaming_service.create_session(
            websocket=mock_websocket,
            transcriber_type="vosk",
            config={"buffer_size": 1024}
        )
        
        # Send multiple small chunks
        for i in range(5):
            chunk = sample_audio_data[:100]  # Small chunk
            await streaming_service.process_audio_chunk(session_id, chunk)
        
        stats = await streaming_service.get_session_stats(session_id)
        assert stats["chunks_processed"] == 5
        
        # Buffer should be managed efficiently
        resources = await streaming_service.get_resource_usage(session_id)
        assert resources["audio_buffer_size"] <= 1024

    @pytest.mark.asyncio
    async def test_transcriber_switching(self, streaming_service, mock_websocket):
        """Test switching transcribers mid-session."""
        session_id = await streaming_service.create_session(
            websocket=mock_websocket,
            transcriber_type="vosk",
            config={}
        )
        
        # Switch to different transcriber
        await streaming_service.switch_transcriber(session_id, "whisper", {"model": "base"})
        
        session_info = await streaming_service.get_session_info(session_id)
        assert session_info["transcriber_type"] == "whisper"
        assert session_info["config"]["model"] == "base"