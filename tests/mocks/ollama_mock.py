"""Mock Ollama service for testing."""

import asyncio
import json
import random
from typing import Dict, Any, List, Optional, AsyncGenerator
from unittest.mock import AsyncMock
import aiohttp


class MockOllamaResponse:
    """Mock response object for Ollama API."""
    
    def __init__(self, content: str, status_code: int = 200, stream: bool = False):
        self.content = content
        self.status_code = status_code
        self.stream = stream
        self.headers = {"content-type": "application/json"}
    
    def json(self) -> Dict[str, Any]:
        """Return JSON response."""
        if self.status_code == 200:
            if self.stream:
                return {
                    "model": "llama2",
                    "created_at": "2023-08-04T19:22:45.499127Z",
                    "response": self.content,
                    "done": True,
                    "total_duration": 5589157167,
                    "load_duration": 3013701500,
                    "prompt_eval_count": 46,
                    "prompt_eval_duration": 1160282000,
                    "eval_count": 113,
                    "eval_duration": 1408557000
                }
            else:
                return {
                    "model": "llama2",
                    "created_at": "2023-08-04T19:22:45.499127Z",
                    "response": self.content,
                    "done": True,
                    "context": [1, 2, 3],  # Mock context tokens
                    "total_duration": 5589157167,
                    "load_duration": 3013701500,
                    "prompt_eval_count": 46,
                    "prompt_eval_duration": 1160282000,
                    "eval_count": 113,
                    "eval_duration": 1408557000
                }
        else:
            return {
                "error": "Mock Ollama error response"
            }
    
    async def text(self) -> str:
        """Return text response for aiohttp compatibility."""
        if self.stream:
            # Return streaming format
            lines = []
            words = self.content.split()
            for i, word in enumerate(words):
                chunk = {
                    "model": "llama2",
                    "created_at": "2023-08-04T19:22:45.499127Z",
                    "response": word + (" " if i < len(words) - 1 else ""),
                    "done": i == len(words) - 1
                }
                lines.append(json.dumps(chunk))
            return "\n".join(lines)
        else:
            return json.dumps(self.json())


class MockOllamaClient:
    """Mock Ollama client for testing."""
    
    def __init__(self, fail_after: Optional[int] = None, delay: float = 0.1, base_url: str = "http://localhost:11434"):
        """
        Initialize mock client.
        
        Args:
            fail_after: Fail after this many requests
            delay: Artificial delay to simulate processing time
            base_url: Mock base URL for Ollama service
        """
        self.call_count = 0
        self.fail_after = fail_after
        self.delay = delay
        self.base_url = base_url
        self.call_history: List[Dict[str, Any]] = []
        self._available_models = ["llama2", "mistral", "codellama", "neural-chat"]
    
    async def generate(
        self,
        model: str,
        prompt: str,
        stream: bool = False,
        options: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> MockOllamaResponse:
        """Mock text generation."""
        await asyncio.sleep(self.delay)
        
        self.call_count += 1
        
        # Record call for testing
        call_record = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": options or {},
            "kwargs": kwargs
        }
        self.call_history.append(call_record)
        
        # Simulate failure if configured
        if self.fail_after and self.call_count > self.fail_after:
            return MockOllamaResponse("", status_code=500)
        
        # Check if model is available
        if model not in self._available_models:
            return MockOllamaResponse("", status_code=404)
        
        # Generate mock response based on prompt
        mock_response = self._generate_mock_response(prompt, model)
        return MockOllamaResponse(mock_response, stream=stream)
    
    async def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        stream: bool = False,
        options: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> MockOllamaResponse:
        """Mock chat completion."""
        # Convert messages to prompt for processing
        prompt = ""
        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")
            if role == "system":
                prompt += f"System: {content}\n"
            elif role == "user":
                prompt += f"User: {content}\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n"
        
        return await self.generate(model, prompt, stream=stream, options=options, **kwargs)
    
    async def list_models(self) -> Dict[str, Any]:
        """Mock model listing."""
        await asyncio.sleep(0.1)
        
        return {
            "models": [
                {
                    "name": model,
                    "modified_at": "2023-08-04T19:22:45.499127Z",
                    "size": random.randint(1000000000, 8000000000),  # Random size
                    "digest": f"sha256:{random.getrandbits(256):064x}"
                }
                for model in self._available_models
            ]
        }
    
    async def pull_model(self, model: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Mock model pulling with progress updates."""
        total_size = random.randint(1000000000, 4000000000)
        chunk_size = total_size // 10
        
        for i in range(0, total_size, chunk_size):
            await asyncio.sleep(0.1)
            yield {
                "status": "downloading",
                "digest": f"sha256:{random.getrandbits(256):064x}",
                "total": total_size,
                "completed": min(i + chunk_size, total_size)
            }
        
        yield {
            "status": "success",
            "digest": f"sha256:{random.getrandbits(256):064x}",
            "total": total_size,
            "completed": total_size
        }
    
    def _generate_mock_response(self, prompt: str, model: str) -> str:
        """Generate appropriate mock response based on prompt and model."""
        prompt_lower = prompt.lower()
        
        # Medical-specific responses
        if "medical" in prompt_lower or "patient" in prompt_lower or "doctor" in prompt_lower:
            if "soap" in prompt_lower:
                return """**SOAP Note:**

**Subjective:**
Patient presents with complaints as described in the provided transcript.

**Objective:**
Physical examination findings and vital signs as documented.

**Assessment:**
Clinical assessment based on patient presentation.

**Plan:**
Treatment recommendations and follow-up as discussed."""
            
            elif "summary" in prompt_lower:
                return "This medical encounter involved a patient consultation with discussion of symptoms, examination findings, and treatment planning."
            
            elif "clean" in prompt_lower or "correct" in prompt_lower:
                return "Cleaned and corrected medical transcript with proper medical terminology and formatting."
        
        # Code-related responses (for codellama model)
        elif model == "codellama" and ("code" in prompt_lower or "function" in prompt_lower):
            return """```python
def example_function():
    \"\"\"Mock code response from Ollama.\"\"\"
    return "Generated by mock Ollama CodeLlama"
```"""
        
        # General responses based on model
        elif model == "mistral":
            return f"Mistral model response: {prompt[:100]}..."
        elif model == "neural-chat":
            return f"Neural Chat response: I understand you're asking about {prompt[:50]}..."
        else:  # llama2 or default
            return f"Llama2 response: Based on your prompt about {prompt[:50]}..., here's my analysis."
    
    def reset_history(self):
        """Reset call history for testing."""
        self.call_history.clear()
        self.call_count = 0
    
    def add_model(self, model_name: str):
        """Add a model to available models list."""
        if model_name not in self._available_models:
            self._available_models.append(model_name)
    
    def remove_model(self, model_name: str):
        """Remove a model from available models list."""
        if model_name in self._available_models:
            self._available_models.remove(model_name)


class MockOllamaProvider:
    """Mock Ollama provider that mimics the real provider interface."""
    
    def __init__(self, client: Optional[MockOllamaClient] = None):
        self.client = client or MockOllamaClient()
        self._model_name = "llama2"
        self._base_url = "http://localhost:11434"
    
    async def generate_completion(self, prompt: str, **kwargs) -> str:
        """Generate completion using mock client."""
        model = kwargs.get("model", self._model_name)
        stream = kwargs.get("stream", False)
        options = kwargs.get("options", {})
        
        response = await self.client.generate(
            model=model,
            prompt=prompt,
            stream=stream,
            options=options
        )
        
        if response.status_code != 200:
            raise Exception(f"Mock Ollama API error: {response.status_code}")
        
        response_data = response.json()
        return response_data["response"]
    
    async def generate_note(self, transcript: str, **kwargs) -> str:
        """Generate medical note using mock client."""
        prompt = f"Generate a comprehensive medical note from this transcript: {transcript}"
        return await self.generate_completion(prompt, **kwargs)
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Chat completion using mock client."""
        model = kwargs.get("model", self._model_name)
        response = await self.client.chat(model=model, messages=messages, **kwargs)
        
        if response.status_code != 200:
            raise Exception(f"Mock Ollama chat error: {response.status_code}")
        
        response_data = response.json()
        return response_data["response"]
    
    async def is_available(self) -> bool:
        """Check if Ollama service is available (always True for mock)."""
        return True
    
    async def list_models(self) -> List[str]:
        """List available models."""
        models_data = await self.client.list_models()
        return [model["name"] for model in models_data["models"]]
    
    def get_call_history(self) -> List[Dict[str, Any]]:
        """Get call history for testing."""
        return self.client.call_history
    
    def reset_history(self):
        """Reset call history."""
        self.client.reset_history()


# Factory function for easy mock creation
def create_ollama_mock(
    fail_after: Optional[int] = None,
    delay: float = 0.1,
    base_url: str = "http://localhost:11434"
) -> MockOllamaProvider:
    """Create a mock Ollama provider with specified behavior."""
    client = MockOllamaClient(fail_after=fail_after, delay=delay, base_url=base_url)
    return MockOllamaProvider(client)


# Pytest fixtures
import pytest

@pytest.fixture
def ollama_mock():
    """Pytest fixture for Ollama mock."""
    return create_ollama_mock()


@pytest.fixture
def ollama_mock_with_failures():
    """Pytest fixture for Ollama mock that fails after 3 requests."""
    return create_ollama_mock(fail_after=3)


@pytest.fixture
def ollama_mock_slow():
    """Pytest fixture for Ollama mock with artificial delay."""
    return create_ollama_mock(delay=2.0)


@pytest.fixture
def ollama_mock_unavailable():
    """Pytest fixture for Ollama mock that's unavailable."""
    mock = create_ollama_mock()
    mock.client._available_models = []  # No models available
    return mock