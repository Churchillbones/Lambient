"""Integration tests for agent-based workflow."""

import asyncio
from unittest.mock import patch, MagicMock

import pytest

from src.llm.agents.transcription_cleaner import TranscriptionCleanerAgent
from src.llm.agents.medical_extractor import MedicalExtractorAgent
from src.llm.agents.clinical_writer import ClinicalWriterAgent
from src.llm.agents.quality_reviewer import QualityReviewerAgent
from src.llm.pipeline.orchestrator import LLMOrchestrator
from tests.mocks.azure_openai_mock import create_azure_openai_mock
from tests.mocks.ollama_mock import create_ollama_mock


class TestAgentWorkflowIntegration:
    """Integration tests for the complete agent-based workflow."""
    
    @pytest.fixture
    def sample_medical_transcript(self):
        """Sample medical transcript for testing."""
        return """
        Doctor: Good morning, what brings you in today?
        Patient: I've been having headaches for the past week. They're really bothering me.
        Doctor: Can you describe the headaches? Are they sharp or dull?
        Patient: They're mostly dull, but sometimes they get really sharp, especially behind my eyes.
        Doctor: Have you noticed any triggers? Like stress, certain foods, or lack of sleep?
        Patient: Now that you mention it, they do seem worse when I'm stressed at work.
        Doctor: Any nausea or sensitivity to light?
        Patient: Yes, bright lights make them much worse. And I do feel nauseous sometimes.
        Doctor: Based on your symptoms, this sounds like it could be tension headaches, possibly with some migraine features. Let's start with a mild pain reliever and some lifestyle modifications.
        Patient: Okay, what kind of lifestyle changes?
        Doctor: Try to manage stress better, maintain regular sleep patterns, and avoid known triggers. I'll also prescribe a medication for when the headaches are severe.
        """
    
    @pytest.mark.asyncio
    async def test_complete_agent_workflow_azure_openai(self, sample_medical_transcript):
        """Test complete agent workflow using Azure OpenAI."""
        
        with patch('src.core.providers.azure_openai_provider.AzureOpenAIProvider') as mock_provider_class:
            mock_provider = create_azure_openai_mock()
            mock_provider_class.return_value = mock_provider
            
            # Step 1: Clean transcription
            cleaner_agent = TranscriptionCleanerAgent()
            with patch.object(cleaner_agent, 'llm_provider', mock_provider):
                cleaned_transcript = await cleaner_agent.process(sample_medical_transcript)
                
                assert isinstance(cleaned_transcript, str)
                assert len(cleaned_transcript) > 0
                assert len(cleaned_transcript) <= len(sample_medical_transcript) * 1.2  # Shouldn't grow too much
            
            # Step 2: Extract medical entities
            extractor_agent = MedicalExtractorAgent()
            with patch.object(extractor_agent, 'llm_provider', mock_provider):
                medical_entities = await extractor_agent.process(cleaned_transcript)
                
                assert isinstance(medical_entities, dict)
                assert any(key in medical_entities for key in ["symptoms", "conditions", "medications", "procedures"])
            
            # Step 3: Generate clinical note
            writer_agent = ClinicalWriterAgent()
            with patch.object(writer_agent, 'llm_provider', mock_provider):
                clinical_note = await writer_agent.process(
                    transcript=cleaned_transcript,
                    entities=medical_entities,
                    note_type="soap"
                )
                
                assert isinstance(clinical_note, str)
                assert len(clinical_note) > 100  # Should be substantial
                assert "soap" in clinical_note.lower() or "subjective" in clinical_note.lower()
            
            # Step 4: Quality review
            reviewer_agent = QualityReviewerAgent()
            with patch.object(reviewer_agent, 'llm_provider', mock_provider):
                quality_report = await reviewer_agent.process(
                    original_transcript=sample_medical_transcript,
                    generated_note=clinical_note
                )
                
                assert isinstance(quality_report, dict)
                assert "score" in quality_report
                assert "recommendations" in quality_report
                assert 0 <= quality_report["score"] <= 1
    
    @pytest.mark.asyncio
    async def test_complete_agent_workflow_ollama(self, sample_medical_transcript):
        """Test complete agent workflow using Ollama."""
        
        with patch('src.core.providers.ollama_provider.OllamaProvider') as mock_provider_class:
            mock_provider = create_ollama_mock()
            mock_provider_class.return_value = mock_provider
            
            # Initialize agents with Ollama provider
            agents = {
                "cleaner": TranscriptionCleanerAgent(),
                "extractor": MedicalExtractorAgent(),
                "writer": ClinicalWriterAgent(),
                "reviewer": QualityReviewerAgent()
            }
            
            # Patch all agents to use mock provider
            for agent in agents.values():
                with patch.object(agent, 'llm_provider', mock_provider):
                    pass
            
            # Execute workflow
            cleaned_transcript = await agents["cleaner"].process(sample_medical_transcript)
            assert isinstance(cleaned_transcript, str)
            
            medical_entities = await agents["extractor"].process(cleaned_transcript)
            assert isinstance(medical_entities, dict)
            
            clinical_note = await agents["writer"].process(
                transcript=cleaned_transcript,
                entities=medical_entities,
                note_type="soap"
            )
            assert isinstance(clinical_note, str)
            
            quality_report = await agents["reviewer"].process(
                original_transcript=sample_medical_transcript,
                generated_note=clinical_note
            )
            assert isinstance(quality_report, dict)
    
    @pytest.mark.asyncio
    async def test_orchestrated_agent_workflow(self, sample_medical_transcript):
        """Test agent workflow through the orchestrator."""
        
        with patch('src.core.providers.azure_openai_provider.AzureOpenAIProvider') as mock_provider_class:
            mock_provider = create_azure_openai_mock()
            mock_provider_class.return_value = mock_provider
            
            # Use orchestrator to manage the complete workflow
            orchestrator = LLMOrchestrator()
            
            with patch.object(orchestrator, '_get_llm_provider', return_value=mock_provider):
                result = await orchestrator.process_transcription(
                    transcription=sample_medical_transcript,
                    note_type="soap",
                    patient_context={
                        "patient_id": "TEST_001",
                        "provider": "Dr. Test"
                    }
                )
                
                # Verify orchestrated result structure
                assert isinstance(result, dict)
                assert "content" in result
                assert "metadata" in result
                assert "quality_score" in result
                assert "processing_steps" in result
                
                # Verify content quality
                assert len(result["content"]) > 100
                assert 0 <= result["quality_score"] <= 1
                
                # Verify metadata preservation
                assert result["metadata"]["patient_id"] == "TEST_001"
                assert result["metadata"]["provider"] == "Dr. Test"
                
                # Verify processing steps are recorded
                assert len(result["processing_steps"]) > 0
                expected_steps = ["cleaning", "extraction", "writing", "review"]
                for step in expected_steps:
                    assert any(step in ps["name"].lower() for ps in result["processing_steps"])
    
    @pytest.mark.asyncio
    async def test_agent_workflow_with_different_note_types(self, sample_medical_transcript):
        """Test agent workflow with different note types."""
        
        note_types = ["soap", "summary", "diagnostic", "treatment_plan"]
        
        with patch('src.core.providers.azure_openai_provider.AzureOpenAIProvider') as mock_provider_class:
            mock_provider = create_azure_openai_mock()
            mock_provider_class.return_value = mock_provider
            
            orchestrator = LLMOrchestrator()
            
            for note_type in note_types:
                with patch.object(orchestrator, '_get_llm_provider', return_value=mock_provider):
                    result = await orchestrator.process_transcription(
                        transcription=sample_medical_transcript,
                        note_type=note_type,
                        patient_context={}
                    )
                    
                    assert isinstance(result, dict)
                    assert "content" in result
                    assert len(result["content"]) > 50
                    
                    # Verify note type is reflected in content or metadata
                    assert (
                        note_type.lower() in result["content"].lower() or
                        result["metadata"]["note_type"] == note_type
                    )
    
    @pytest.mark.asyncio
    async def test_agent_workflow_error_handling(self, sample_medical_transcript):
        """Test error handling in agent workflow."""
        
        with patch('src.core.providers.azure_openai_provider.AzureOpenAIProvider') as mock_provider_class:
            # Create provider that fails after 2 calls
            mock_provider = create_azure_openai_mock(fail_after=2)
            mock_provider_class.return_value = mock_provider
            
            orchestrator = LLMOrchestrator()
            
            with patch.object(orchestrator, '_get_llm_provider', return_value=mock_provider):
                # First request should succeed (uses 2 calls)
                result1 = await orchestrator.process_transcription(
                    transcription=sample_medical_transcript[:100],  # Shorter to use fewer calls
                    note_type="summary",
                    patient_context={}
                )
                assert isinstance(result1, dict)
                
                # Subsequent requests should handle errors gracefully
                try:
                    result2 = await orchestrator.process_transcription(
                        transcription=sample_medical_transcript,
                        note_type="soap",
                        patient_context={}
                    )
                    # If no exception, should have error handling info
                    assert "error" in result2 or "partial" in result2
                except Exception as e:
                    # Exception should be descriptive
                    assert "llm" in str(e).lower() or "provider" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_agent_workflow_concurrent_processing(self, sample_medical_transcript):
        """Test concurrent agent processing."""
        
        with patch('src.core.providers.azure_openai_provider.AzureOpenAIProvider') as mock_provider_class:
            mock_provider = create_azure_openai_mock(delay=0.1)  # Small delay to test concurrency
            mock_provider_class.return_value = mock_provider
            
            orchestrator = LLMOrchestrator()
            
            # Create multiple concurrent transcription tasks
            tasks = []
            for i in range(3):
                task = orchestrator.process_transcription(
                    transcription=f"{sample_medical_transcript} Session {i}",
                    note_type="summary",
                    patient_context={"session_id": f"session_{i}"}
                )
                tasks.append(task)
            
            # Execute concurrently
            with patch.object(orchestrator, '_get_llm_provider', return_value=mock_provider):
                import time
                start_time = time.time()
                results = await asyncio.gather(*tasks)
                end_time = time.time()
                
                # Verify all tasks completed
                assert len(results) == 3
                for i, result in enumerate(results):
                    assert isinstance(result, dict)
                    assert result["metadata"]["session_id"] == f"session_{i}"
                
                # Should complete faster than sequential processing
                total_time = end_time - start_time
                assert total_time < 2.0  # Should be much faster than 3 sequential calls
    
    @pytest.mark.asyncio
    async def test_agent_workflow_quality_thresholds(self, sample_medical_transcript):
        """Test quality threshold enforcement in agent workflow."""
        
        with patch('src.core.providers.azure_openai_provider.AzureOpenAIProvider') as mock_provider_class:
            mock_provider = create_azure_openai_mock()
            mock_provider_class.return_value = mock_provider
            
            orchestrator = LLMOrchestrator()
            
            # Set quality threshold
            quality_threshold = 0.8
            
            with patch.object(orchestrator, '_get_llm_provider', return_value=mock_provider):
                result = await orchestrator.process_transcription(
                    transcription=sample_medical_transcript,
                    note_type="soap",
                    patient_context={},
                    quality_threshold=quality_threshold
                )
                
                # If quality is below threshold, should trigger retry or enhancement
                if result["quality_score"] < quality_threshold:
                    assert "enhanced" in result or "retry_count" in result["metadata"]
                
                # Final result should meet or note failure to meet threshold
                assert (
                    result["quality_score"] >= quality_threshold or
                    "quality_warning" in result["metadata"]
                )
    
    @pytest.mark.asyncio
    async def test_agent_workflow_with_context_injection(self, sample_medical_transcript):
        """Test agent workflow with rich context injection."""
        
        with patch('src.core.providers.azure_openai_provider.AzureOpenAIProvider') as mock_provider_class:
            mock_provider = create_azure_openai_mock()
            mock_provider_class.return_value = mock_provider
            
            # Rich patient context
            patient_context = {
                "patient_id": "P12345",
                "age": 45,
                "gender": "female",
                "medical_history": ["hypertension", "diabetes"],
                "current_medications": ["lisinopril", "metformin"],
                "allergies": ["penicillin"],
                "provider": "Dr. Smith",
                "specialty": "Internal Medicine",
                "encounter_type": "follow-up"
            }
            
            orchestrator = LLMOrchestrator()
            
            with patch.object(orchestrator, '_get_llm_provider', return_value=mock_provider):
                result = await orchestrator.process_transcription(
                    transcription=sample_medical_transcript,
                    note_type="soap",
                    patient_context=patient_context
                )
                
                # Verify context is incorporated
                content = result["content"].lower()
                metadata = result["metadata"]
                
                # Context should be preserved in metadata
                assert metadata["patient_id"] == "P12345"
                assert metadata["provider"] == "Dr. Smith"
                assert metadata["specialty"] == "Internal Medicine"
                
                # Medical history might be referenced in content or metadata
                assert (
                    any(condition in content for condition in ["hypertension", "diabetes"]) or
                    "medical_history" in metadata
                )