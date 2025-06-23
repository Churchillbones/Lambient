"""Performance tests for streaming transcription."""

import asyncio
import time
import statistics
from typing import List, Dict, Any
from unittest.mock import patch

import pytest
import psutil

from src.core.services.streaming_service import StreamingService
from tests.mocks.vosk_mock import create_vosk_mock
from tests.mocks.azure_speech_mock import create_azure_speech_mock


class TestStreamingPerformance:
    """Performance benchmarks for streaming transcription."""
    
    @pytest.fixture
    def large_audio_data(self):
        """Generate large audio data for performance testing."""
        # Simulate 30 seconds of audio data (16kHz, 16-bit, mono)
        return b"mock_audio_chunk" * 10000  # ~140KB of data
    
    @pytest.fixture
    def streaming_service(self):
        """Create streaming service for performance testing."""
        return StreamingService()
    
    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_single_session_throughput(self, streaming_service, large_audio_data, benchmark):
        """Benchmark single session throughput."""
        
        with patch('src.asr.transcribers.vosk.VoskTranscriber') as mock_vosk_class:
            mock_vosk = create_vosk_mock()
            mock_vosk_class.return_value = mock_vosk
            
            mock_websocket = MockWebSocket()
            
            async def process_session():
                # Create session
                session_id = await streaming_service.create_session(
                    websocket=mock_websocket,
                    transcriber_type="vosk",
                    config={"language": "en"}
                )
                
                # Process audio in chunks
                chunk_size = 4000
                chunks_processed = 0
                
                for i in range(0, len(large_audio_data), chunk_size):
                    chunk = large_audio_data[i:i + chunk_size]
                    await streaming_service.process_audio_chunk(session_id, chunk)
                    chunks_processed += 1
                
                # Clean up
                await streaming_service.close_session(session_id)
                
                return chunks_processed
            
            # Benchmark the processing
            result = await benchmark.pedantic(process_session, rounds=3, iterations=1)
            
            # Verify performance metrics
            assert result > 0
            assert benchmark.stats["mean"] < 5.0  # Should complete within 5 seconds
    
    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_concurrent_sessions_scalability(self, streaming_service, large_audio_data):
        """Test scalability with multiple concurrent sessions."""
        
        with patch('src.asr.transcribers.vosk.VoskTranscriber') as mock_vosk_class:
            mock_vosk = create_vosk_mock()
            mock_vosk_class.return_value = mock_vosk
            
            session_counts = [1, 5, 10, 20]
            results = {}
            
            for session_count in session_counts:
                mock_websockets = [MockWebSocket() for _ in range(session_count)]
                
                # Measure time for concurrent sessions
                start_time = time.time()
                
                # Create sessions
                session_tasks = [
                    streaming_service.create_session(
                        websocket=ws,
                        transcriber_type="vosk",
                        config={"language": "en"}
                    )
                    for ws in mock_websockets
                ]
                session_ids = await asyncio.gather(*session_tasks)
                
                # Process audio concurrently
                audio_tasks = []
                chunk_size = 2000
                
                for session_id in session_ids:
                    for i in range(0, min(len(large_audio_data), 8000), chunk_size):
                        chunk = large_audio_data[i:i + chunk_size]
                        task = streaming_service.process_audio_chunk(session_id, chunk)
                        audio_tasks.append(task)
                
                await asyncio.gather(*audio_tasks)
                
                # Clean up sessions
                cleanup_tasks = [
                    streaming_service.close_session(sid) for sid in session_ids
                ]
                await asyncio.gather(*cleanup_tasks)
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                results[session_count] = {
                    "processing_time": processing_time,
                    "sessions": session_count,
                    "throughput": session_count / processing_time
                }
            
            # Verify scalability
            assert results[1]["processing_time"] < 3.0  # Single session should be fast
            assert results[5]["throughput"] > results[1]["throughput"] * 2  # Should scale reasonably
            
            # Log results for analysis
            for count, result in results.items():
                print(f"Sessions: {count}, Time: {result['processing_time']:.2f}s, "
                      f"Throughput: {result['throughput']:.2f} sessions/sec")
    
    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_memory_usage_under_load(self, streaming_service, large_audio_data):
        """Test memory usage patterns under load."""
        
        with patch('src.asr.transcribers.vosk.VoskTranscriber') as mock_vosk_class:
            mock_vosk = create_vosk_mock()
            mock_vosk_class.return_value = mock_vosk
            
            process = psutil.Process()
            memory_measurements = []
            
            # Baseline memory
            baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_measurements.append(baseline_memory)
            
            mock_websockets = [MockWebSocket() for _ in range(10)]
            
            # Create sessions and measure memory
            session_tasks = [
                streaming_service.create_session(
                    websocket=ws,
                    transcriber_type="vosk",
                    config={"language": "en"}
                )
                for ws in mock_websockets
            ]
            session_ids = await asyncio.gather(*session_tasks)
            
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_measurements.append(current_memory)
            
            # Process audio and measure memory periodically
            chunk_size = 4000
            for i in range(0, len(large_audio_data), chunk_size):
                chunk = large_audio_data[i:i + chunk_size]
                
                # Process on all sessions
                tasks = [
                    streaming_service.process_audio_chunk(sid, chunk)
                    for sid in session_ids
                ]
                await asyncio.gather(*tasks)
                
                # Measure memory every few chunks
                if i % (chunk_size * 5) == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024
                    memory_measurements.append(current_memory)
            
            # Clean up and measure final memory
            cleanup_tasks = [
                streaming_service.close_session(sid) for sid in session_ids
            ]
            await asyncio.gather(*cleanup_tasks)
            
            # Force garbage collection
            import gc
            gc.collect()
            await asyncio.sleep(0.1)
            
            final_memory = process.memory_info().rss / 1024 / 1024
            memory_measurements.append(final_memory)
            
            # Analyze memory usage
            max_memory = max(memory_measurements)
            memory_growth = max_memory - baseline_memory
            memory_leak = final_memory - baseline_memory
            
            print(f"Baseline memory: {baseline_memory:.2f} MB")
            print(f"Max memory: {max_memory:.2f} MB")
            print(f"Memory growth: {memory_growth:.2f} MB")
            print(f"Memory leak: {memory_leak:.2f} MB")
            
            # Verify memory constraints
            assert memory_growth < 200  # Should not use more than 200MB additional
            assert memory_leak < 50    # Should not leak more than 50MB
    
    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_latency_distribution(self, streaming_service, large_audio_data):
        """Test latency distribution for real-time requirements."""
        
        with patch('src.asr.transcribers.vosk.VoskTranscriber') as mock_vosk_class:
            mock_vosk = create_vosk_mock()
            mock_vosk_class.return_value = mock_vosk
            
            mock_websocket = MockWebSocket()
            
            # Create session
            session_id = await streaming_service.create_session(
                websocket=mock_websocket,
                transcriber_type="vosk",
                config={"language": "en"}
            )
            
            # Measure latency for many chunks
            latencies = []
            chunk_size = 2000
            
            for i in range(0, min(len(large_audio_data), 20000), chunk_size):
                chunk = large_audio_data[i:i + chunk_size]
                
                start_time = time.time()
                await streaming_service.process_audio_chunk(session_id, chunk)
                end_time = time.time()
                
                latency_ms = (end_time - start_time) * 1000
                latencies.append(latency_ms)
            
            # Analyze latency distribution
            mean_latency = statistics.mean(latencies)
            median_latency = statistics.median(latencies)
            p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
            p99_latency = sorted(latencies)[int(len(latencies) * 0.99)]
            max_latency = max(latencies)
            
            print(f"Latency statistics:")
            print(f"  Mean: {mean_latency:.2f} ms")
            print(f"  Median: {median_latency:.2f} ms")
            print(f"  P95: {p95_latency:.2f} ms")
            print(f"  P99: {p99_latency:.2f} ms")
            print(f"  Max: {max_latency:.2f} ms")
            
            # Real-time requirements (for streaming audio)
            assert mean_latency < 500     # Mean latency < 500ms
            assert p95_latency < 1000     # 95% of requests < 1s
            assert p99_latency < 2000     # 99% of requests < 2s
            
            # Clean up
            await streaming_service.close_session(session_id)
    
    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_transcriber_comparison(self, streaming_service, large_audio_data):
        """Compare performance of different transcribers."""
        
        transcribers = [
            ("vosk", create_vosk_mock()),
            ("azure_speech", create_azure_speech_mock())
        ]
        
        results = {}
        
        for transcriber_name, mock_transcriber in transcribers:
            patch_path = f'src.asr.transcribers.{transcriber_name}.{transcriber_name.title().replace("_", "")}Transcriber'
            
            with patch(patch_path) as mock_class:
                mock_class.return_value = mock_transcriber
                
                mock_websocket = MockWebSocket()
                
                # Measure processing time
                start_time = time.time()
                
                session_id = await streaming_service.create_session(
                    websocket=mock_websocket,
                    transcriber_type=transcriber_name,
                    config={"language": "en"}
                )
                
                # Process audio chunks
                chunk_size = 4000
                chunks_processed = 0
                
                for i in range(0, min(len(large_audio_data), 12000), chunk_size):
                    chunk = large_audio_data[i:i + chunk_size]
                    await streaming_service.process_audio_chunk(session_id, chunk)
                    chunks_processed += 1
                
                await streaming_service.close_session(session_id)
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                results[transcriber_name] = {
                    "processing_time": processing_time,
                    "chunks_processed": chunks_processed,
                    "throughput": chunks_processed / processing_time
                }
        
        # Compare results
        for name, result in results.items():
            print(f"{name}: {result['processing_time']:.2f}s, "
                  f"Throughput: {result['throughput']:.2f} chunks/sec")
        
        # All transcribers should complete in reasonable time
        for result in results.values():
            assert result["processing_time"] < 10.0
            assert result["throughput"] > 0.5
    
    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_session_lifecycle_performance(self, streaming_service):
        """Test performance of session creation and cleanup."""
        
        with patch('src.asr.transcribers.vosk.VoskTranscriber') as mock_vosk_class:
            mock_vosk = create_vosk_mock()
            mock_vosk_class.return_value = mock_vosk
            
            # Test rapid session creation/destruction
            session_count = 100
            creation_times = []
            cleanup_times = []
            
            for _ in range(session_count):
                mock_websocket = MockWebSocket()
                
                # Measure session creation time
                start_time = time.time()
                session_id = await streaming_service.create_session(
                    websocket=mock_websocket,
                    transcriber_type="vosk",
                    config={"language": "en"}
                )
                creation_time = time.time() - start_time
                creation_times.append(creation_time * 1000)  # Convert to ms
                
                # Measure session cleanup time
                start_time = time.time()
                await streaming_service.close_session(session_id)
                cleanup_time = time.time() - start_time
                cleanup_times.append(cleanup_time * 1000)  # Convert to ms
            
            # Analyze timing
            avg_creation_time = statistics.mean(creation_times)
            avg_cleanup_time = statistics.mean(cleanup_times)
            max_creation_time = max(creation_times)
            max_cleanup_time = max(cleanup_times)
            
            print(f"Session lifecycle performance:")
            print(f"  Avg creation time: {avg_creation_time:.2f} ms")
            print(f"  Max creation time: {max_creation_time:.2f} ms")
            print(f"  Avg cleanup time: {avg_cleanup_time:.2f} ms")
            print(f"  Max cleanup time: {max_cleanup_time:.2f} ms")
            
            # Performance requirements
            assert avg_creation_time < 100   # Average creation < 100ms
            assert max_creation_time < 500   # Max creation < 500ms
            assert avg_cleanup_time < 50     # Average cleanup < 50ms
            assert max_cleanup_time < 200    # Max cleanup < 200ms


class MockWebSocket:
    """Mock WebSocket for performance testing."""
    
    def __init__(self):
        self.messages_sent = []
        self.closed = False
    
    async def send_text(self, data: str):
        """Mock send text."""
        self.messages_sent.append(data)
    
    async def send_bytes(self, data: bytes):
        """Mock send bytes."""
        self.messages_sent.append(data)
    
    async def close(self):
        """Mock close."""
        self.closed = True


if __name__ == "__main__":
    # Run specific performance tests
    pytest.main([__file__, "-v", "-m", "benchmark", "--benchmark-only"])