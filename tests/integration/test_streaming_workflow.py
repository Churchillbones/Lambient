"""Integration tests for streaming transcription workflow."""

import asyncio
import json
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
import websockets
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket

from src.core.services.streaming_service import StreamingService
from src.core.services.audio_service import AudioService
from src.asr.streaming.websocket import WebSocketHandler
from tests.mocks.azure_speech_mock import create_azure_speech_mock
from tests.mocks.vosk_mock import create_vosk_mock


class TestStreamingWorkflowIntegration:
    """Integration tests for the complete streaming workflow."""
    
    @pytest.fixture
    async def streaming_service(self):
        """Create streaming service for testing."""
        return StreamingService()
    
    @pytest.fixture
    async def audio_service(self):
        """Create audio service for testing."""
        return AudioService()
    
    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket for testing."""
        mock_ws = MagicMock(spec=WebSocket)
        mock_ws.send_text = AsyncMock()
        mock_ws.send_bytes = AsyncMock()
        mock_ws.receive_text = AsyncMock()
        mock_ws.receive_bytes = AsyncMock()
        mock_ws.close = AsyncMock()
        return mock_ws
    
    @pytest.fixture
    def sample_audio_data(self):
        """Create sample audio data for testing."""
        # Simple PCM audio data simulation
        return b"RIFF" + b"\x00" * 44 + b"mock_audio_data" * 1000
    
    @pytest.mark.asyncio
    async def test_end_to_end_streaming_vosk(
        self, 
        streaming_service,
        audio_service,
        mock_websocket,
        sample_audio_data
    ):
        """Test complete streaming workflow with Vosk transcriber."""
        
        # Mock Vosk transcriber
        with patch('src.asr.transcribers.vosk.VoskTranscriber') as mock_vosk_class:
            mock_vosk = create_vosk_mock()
            mock_vosk_class.return_value = mock_vosk
            
            # Create streaming session
            session_id = await streaming_service.create_session(
                websocket=mock_websocket,
                transcriber_type="vosk",
                config={"language": "en", "model": "vosk-model-en-us-0.22"}
            )
            
            assert session_id is not None
            assert uuid.UUID(session_id)  # Valid UUID
            
            # Send audio chunks and verify responses
            chunk_size = 4000
            chunks_sent = 0
            
            for i in range(0, len(sample_audio_data), chunk_size):
                chunk = sample_audio_data[i:i + chunk_size]
                
                # Process audio chunk
                result = await streaming_service.process_audio_chunk(session_id, chunk)
                
                assert isinstance(result, dict)
                assert "type" in result  # Should have partial or final result
                chunks_sent += 1
            
            # Verify session statistics
            stats = await streaming_service.get_session_stats(session_id)
            assert stats["chunks_processed"] == chunks_sent
            assert stats["total_audio_duration"] > 0
            
            # Close session
            await streaming_service.close_session(session_id)
            
            # Verify session is removed
            active_sessions = await streaming_service.get_active_sessions()
            assert session_id not in active_sessions
    
    @pytest.mark.asyncio
    async def test_end_to_end_streaming_azure_speech(
        self,
        streaming_service,
        mock_websocket,
        sample_audio_data
    ):
        """Test complete streaming workflow with Azure Speech transcriber."""
        
        # Mock Azure Speech transcriber
        with patch('src.asr.transcribers.azure_speech.AzureSpeechTranscriber') as mock_azure_class:
            mock_azure = create_azure_speech_mock()
            mock_azure_class.return_value = mock_azure
            
            # Create streaming session
            session_id = await streaming_service.create_session(
                websocket=mock_websocket,
                transcriber_type="azure_speech",
                config={"language": "en-US", "endpoint": "mock_endpoint"}
            )
            
            # Process audio stream
            chunks_processed = 0
            for i in range(0, len(sample_audio_data), 2000):
                chunk = sample_audio_data[i:i + 2000]
                result = await streaming_service.process_audio_chunk(session_id, chunk)
                
                # Verify result structure
                assert isinstance(result, dict)
                if result.get("type") == "final":
                    assert "text" in result
                    assert "confidence" in result
                elif result.get("type") == "partial":
                    assert "text" in result
                
                chunks_processed += 1
            
            # Verify processing occurred
            assert chunks_processed > 0
            
            # Get final session info
            session_info = await streaming_service.get_session_info(session_id)
            assert session_info["transcriber_type"] == "azure_speech"
            assert session_info["status"] in ["active", "processing"]
            
            # Clean up
            await streaming_service.close_session(session_id)
    
    @pytest.mark.asyncio
    async def test_concurrent_streaming_sessions(
        self,
        streaming_service,
        sample_audio_data
    ):
        """Test multiple concurrent streaming sessions."""
        
        # Create multiple mock WebSockets
        mock_ws1 = MagicMock(spec=WebSocket)
        mock_ws1.send_text = AsyncMock()
        mock_ws2 = MagicMock(spec=WebSocket)
        mock_ws2.send_text = AsyncMock()
        mock_ws3 = MagicMock(spec=WebSocket)
        mock_ws3.send_text = AsyncMock()
        
        # Mock transcribers
        with patch('src.asr.transcribers.vosk.VoskTranscriber') as mock_vosk_class:
            with patch('src.asr.transcribers.azure_speech.AzureSpeechTranscriber') as mock_azure_class:
                mock_vosk_class.return_value = create_vosk_mock()
                mock_azure_class.return_value = create_azure_speech_mock()
                
                # Create multiple sessions concurrently
                session_tasks = [
                    streaming_service.create_session(mock_ws1, "vosk", {"language": "en"}),
                    streaming_service.create_session(mock_ws2, "azure_speech", {"language": "en-US"}),
                    streaming_service.create_session(mock_ws3, "vosk", {"language": "es"})
                ]
                
                session_ids = await asyncio.gather(*session_tasks)
                
                # Verify all sessions created
                assert len(session_ids) == 3
                assert all(uuid.UUID(sid) for sid in session_ids)
                
                # Process audio on all sessions concurrently
                audio_tasks = []
                for session_id in session_ids:
                    task = streaming_service.process_audio_chunk(
                        session_id, 
                        sample_audio_data[:2000]
                    )
                    audio_tasks.append(task)
                
                results = await asyncio.gather(*audio_tasks)
                
                # Verify all sessions processed audio
                assert len(results) == 3
                for result in results:
                    assert isinstance(result, dict)
                
                # Clean up all sessions
                cleanup_tasks = [
                    streaming_service.close_session(sid) for sid in session_ids
                ]
                await asyncio.gather(*cleanup_tasks)
                
                # Verify all sessions removed
                active_sessions = await streaming_service.get_active_sessions()
                for session_id in session_ids:
                    assert session_id not in active_sessions
    
    @pytest.mark.asyncio
    async def test_streaming_error_recovery(
        self,
        streaming_service,
        mock_websocket,
        sample_audio_data
    ):
        """Test error recovery in streaming workflow."""
        
        # Mock transcriber that fails after 2 calls
        with patch('src.asr.transcribers.vosk.VoskTranscriber') as mock_vosk_class:
            mock_vosk = create_vosk_mock()
            
            # Make transcriber fail after 2 successful calls
            original_transcribe = mock_vosk.transcribe_stream
            call_count = 0
            
            async def failing_transcribe(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count > 2:
                    raise Exception("Mock transcription error")
                return await original_transcribe(*args, **kwargs)
            
            mock_vosk.transcribe_stream = failing_transcribe
            mock_vosk_class.return_value = mock_vosk
            
            # Create session
            session_id = await streaming_service.create_session(
                websocket=mock_websocket,
                transcriber_type="vosk",
                config={"language": "en"}
            )
            
            # Process chunks until error occurs
            successful_chunks = 0
            error_occurred = False
            
            for i in range(5):  # Try 5 chunks
                chunk = sample_audio_data[i*1000:(i+1)*1000]
                
                try:
                    result = await streaming_service.process_audio_chunk(session_id, chunk)
                    successful_chunks += 1
                except Exception:
                    error_occurred = True
                    break
            
            # Verify error handling
            assert successful_chunks >= 2  # Should process some chunks successfully
            assert error_occurred or call_count > 2  # Error should occur eventually
            
            # Verify session can still be queried
            session_info = await streaming_service.get_session_info(session_id)
            assert session_info is not None
            
            # Clean up
            await streaming_service.close_session(session_id)
    
    @pytest.mark.asyncio
    async def test_streaming_session_timeout(
        self,
        streaming_service,
        mock_websocket
    ):
        """Test streaming session timeout handling."""
        
        with patch('src.asr.transcribers.vosk.VoskTranscriber') as mock_vosk_class:
            mock_vosk_class.return_value = create_vosk_mock()
            
            # Create session with short timeout
            session_id = await streaming_service.create_session(
                websocket=mock_websocket,
                transcriber_type="vosk",
                config={"language": "en", "session_timeout": 0.1}  # 100ms timeout
            )
            
            # Wait longer than timeout
            await asyncio.sleep(0.2)
            
            # Run cleanup process
            await streaming_service.cleanup_expired_sessions()
            
            # Verify session was removed due to timeout
            active_sessions = await streaming_service.get_active_sessions()
            assert session_id not in active_sessions
    
    @pytest.mark.asyncio
    async def test_websocket_disconnection_handling(
        self,
        streaming_service,
        sample_audio_data
    ):
        """Test handling of WebSocket disconnections."""
        
        # Mock WebSocket that fails on send
        mock_ws = MagicMock(spec=WebSocket)
        mock_ws.send_text = AsyncMock(side_effect=websockets.exceptions.ConnectionClosed(None, None))
        
        with patch('src.asr.transcribers.vosk.VoskTranscriber') as mock_vosk_class:
            mock_vosk_class.return_value = create_vosk_mock()
            
            # Create session
            session_id = await streaming_service.create_session(
                websocket=mock_ws,
                transcriber_type="vosk",
                config={"language": "en"}
            )
            
            # Process audio chunk (should handle WebSocket error gracefully)
            result = await streaming_service.process_audio_chunk(
                session_id, 
                sample_audio_data[:1000]
            )
            
            # Should still return result even if WebSocket send fails
            assert isinstance(result, dict)
            
            # Check session status
            session_info = await streaming_service.get_session_info(session_id)
            assert session_info["status"] in ["disconnected", "error", "active"]
    
    @pytest.mark.asyncio
    async def test_audio_format_validation_in_streaming(
        self,
        streaming_service,
        audio_service,
        mock_websocket
    ):
        """Test audio format validation in streaming workflow."""
        
        with patch('src.asr.transcribers.vosk.VoskTranscriber') as mock_vosk_class:
            mock_vosk_class.return_value = create_vosk_mock()
            
            # Create session
            session_id = await streaming_service.create_session(
                websocket=mock_websocket,
                transcriber_type="vosk",
                config={"language": "en"}
            )
            
            # Test with invalid audio data
            invalid_audio = b"not_valid_audio_data"
            
            # Should handle invalid audio gracefully
            try:
                result = await streaming_service.process_audio_chunk(session_id, invalid_audio)
                # If no exception, result should indicate error or be empty
                assert isinstance(result, dict)
            except Exception as e:
                # Exception handling should be graceful
                assert "audio" in str(e).lower() or "format" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_streaming_performance_metrics(
        self,
        streaming_service,
        mock_websocket,
        sample_audio_data
    ):
        """Test streaming performance metrics collection."""
        
        with patch('src.asr.transcribers.vosk.VoskTranscriber') as mock_vosk_class:
            mock_vosk_class.return_value = create_vosk_mock()
            
            # Create session
            session_id = await streaming_service.create_session(
                websocket=mock_websocket,
                transcriber_type="vosk",
                config={"language": "en"}
            )
            
            # Process multiple chunks to generate metrics
            for i in range(3):
                chunk = sample_audio_data[i*1000:(i+1)*1000]
                await streaming_service.process_audio_chunk(session_id, chunk)
                await asyncio.sleep(0.1)  # Small delay between chunks
            
            # Get performance metrics
            stats = await streaming_service.get_session_stats(session_id)
            
            # Verify metrics are collected
            assert "chunks_processed" in stats
            assert "total_audio_duration" in stats
            assert "average_processing_time" in stats
            assert "total_processing_time" in stats
            
            assert stats["chunks_processed"] == 3
            assert stats["average_processing_time"] > 0
            assert stats["total_processing_time"] > 0
            
            # Get resource usage
            resources = await streaming_service.get_resource_usage(session_id)
            
            assert "memory_usage" in resources
            assert "cpu_usage" in resources
            assert "audio_buffer_size" in resources
            
            # Clean up
            await streaming_service.close_session(session_id)