"""Mock Azure OpenAI service for testing."""

import asyncio
import json
import random
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock


class MockAzureOpenAIResponse:
    """Mock response object for Azure OpenAI API."""
    
    def __init__(self, content: str, status_code: int = 200):
        self.content = content
        self.status_code = status_code
        self.headers = {"content-type": "application/json"}
    
    def json(self) -> Dict[str, Any]:
        """Return JSON response."""
        if self.status_code == 200:
            return {
                "id": f"chatcmpl-{random.randint(1000, 9999)}",
                "object": "chat.completion",
                "created": 1677652288,
                "model": "gpt-35-turbo",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": self.content
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": 50,
                    "completion_tokens": len(self.content.split()),
                    "total_tokens": 50 + len(self.content.split())
                }
            }
        else:
            return {
                "error": {
                    "message": "Mock error response",
                    "type": "mock_error",
                    "code": "mock_error_code"
                }
            }


class MockAzureOpenAIClient:
    """Mock Azure OpenAI client for testing."""
    
    def __init__(self, fail_after: Optional[int] = None, delay: float = 0.1):
        """
        Initialize mock client.
        
        Args:
            fail_after: Fail after this many requests (for testing error handling)
            delay: Artificial delay to simulate network latency
        """
        self.call_count = 0
        self.fail_after = fail_after
        self.delay = delay
        self.call_history: List[Dict[str, Any]] = []
    
    async def chat_completions_create(
        self, 
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> MockAzureOpenAIResponse:
        """Mock chat completion creation."""
        await asyncio.sleep(self.delay)
        
        self.call_count += 1
        
        # Record call for testing
        call_record = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "kwargs": kwargs
        }
        self.call_history.append(call_record)
        
        # Simulate failure if configured
        if self.fail_after and self.call_count > self.fail_after:
            return MockAzureOpenAIResponse("", status_code=500)
        
        # Generate mock response based on input
        user_message = ""
        for message in messages:
            if message.get("role") == "user":
                user_message = message.get("content", "")
                break
        
        mock_response = self._generate_mock_response(user_message)
        return MockAzureOpenAIResponse(mock_response)
    
    def _generate_mock_response(self, user_input: str) -> str:
        """Generate appropriate mock response based on input."""
        user_lower = user_input.lower()
        
        # Medical note generation
        if "soap" in user_lower or "medical note" in user_lower:
            return """
SOAP Note:

Subjective:
Patient presents with chief complaint as described in the transcript.

Objective:
Vital signs stable. Physical examination findings as noted.

Assessment:
Based on the patient presentation and examination findings.

Plan:
Treatment plan to be implemented as discussed.
"""
        
        # Summary generation
        elif "summary" in user_lower or "summarize" in user_lower:
            return "Mock summary of the provided medical transcript focusing on key clinical findings."
        
        # Text cleaning
        elif "clean" in user_lower or "correct" in user_lower:
            return "Cleaned and corrected version of the provided text with proper grammar and formatting."
        
        # Speaker identification
        elif "speaker" in user_lower or "diarization" in user_lower:
            return """
Speaker 1 (Healthcare Provider): Professional medical questions and responses
Speaker 2 (Patient): Patient responses and concerns
"""
        
        # JSON output
        elif "json" in user_lower:
            return json.dumps({
                "result": "mock_json_response",
                "status": "success",
                "data": {"mock": "data"}
            })
        
        # Default response
        else:
            return f"Mock Azure OpenAI response for: {user_input[:50]}..."
    
    def reset_history(self):
        """Reset call history for testing."""
        self.call_history.clear()
        self.call_count = 0


class MockAzureOpenAIProvider:
    """Mock Azure OpenAI provider that mimics the real provider interface."""
    
    def __init__(self, client: Optional[MockAzureOpenAIClient] = None):
        self.client = client or MockAzureOpenAIClient()
        self._model_name = "gpt-35-turbo"
    
    async def generate_completion(self, prompt: str, **kwargs) -> str:
        """Generate completion using mock client."""
        messages = [{"role": "user", "content": prompt}]
        
        response = await self.client.chat_completions_create(
            model=self._model_name,
            messages=messages,
            **kwargs
        )
        
        if response.status_code != 200:
            raise Exception("Mock Azure OpenAI API error")
        
        response_data = response.json()
        return response_data["choices"][0]["message"]["content"]
    
    async def generate_note(self, transcript: str, **kwargs) -> str:
        """Generate medical note using mock client."""
        prompt = f"Generate a medical note from this transcript: {transcript}"
        return await self.generate_completion(prompt, **kwargs)
    
    def get_call_history(self) -> List[Dict[str, Any]]:
        """Get call history for testing."""
        return self.client.call_history
    
    def reset_history(self):
        """Reset call history."""
        self.client.reset_history()


# Factory function for easy mock creation
def create_azure_openai_mock(
    fail_after: Optional[int] = None,
    delay: float = 0.1
) -> MockAzureOpenAIProvider:
    """Create a mock Azure OpenAI provider with specified behavior."""
    client = MockAzureOpenAIClient(fail_after=fail_after, delay=delay)
    return MockAzureOpenAIProvider(client)


# Pytest fixture
import pytest

@pytest.fixture
def azure_openai_mock():
    """Pytest fixture for Azure OpenAI mock."""
    return create_azure_openai_mock()


@pytest.fixture
def azure_openai_mock_with_failures():
    """Pytest fixture for Azure OpenAI mock that fails after 2 requests."""
    return create_azure_openai_mock(fail_after=2)


@pytest.fixture
def azure_openai_mock_slow():
    """Pytest fixture for Azure OpenAI mock with artificial delay."""
    return create_azure_openai_mock(delay=1.0)