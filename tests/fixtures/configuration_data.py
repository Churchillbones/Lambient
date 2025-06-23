"""Configuration test data and fixtures."""

from typing import Dict, Any
import tempfile
import os
from pathlib import Path


# Valid configuration examples
VALID_CONFIGURATIONS = {
    "minimal": {
        "azure": {
            "openai": {
                "endpoint": "https://test.openai.azure.com/",
                "api_key": "test_key_123",
                "deployment_name": "gpt-35-turbo"
            }
        }
    },
    
    "complete": {
        "azure": {
            "openai": {
                "endpoint": "https://test.openai.azure.com/",
                "api_key": "test_openai_key_456",
                "deployment_name": "gpt-35-turbo",
                "api_version": "2023-12-01-preview",
                "temperature": 0.7,
                "max_tokens": 1000
            },
            "speech": {
                "subscription_key": "test_speech_key_789",
                "region": "eastus",
                "language": "en-US",
                "endpoint_id": "custom_endpoint_123"
            }
        },
        "vosk": {
            "model_path": "/opt/vosk/models/vosk-model-en-us-0.22",
            "language": "en",
            "sample_rate": 16000
        },
        "ollama": {
            "base_url": "http://localhost:11434",
            "model": "llama2",
            "temperature": 0.8,
            "timeout": 30
        },
        "security": {
            "encryption_key": "test_encryption_key_abc",
            "enable_audit_logging": True
        },
        "audio": {
            "max_file_size_mb": 100,
            "supported_formats": ["wav", "mp3", "flac"],
            "default_sample_rate": 16000
        },
        "streaming": {
            "max_concurrent_sessions": 50,
            "session_timeout_minutes": 30,
            "buffer_size_kb": 64
        }
    },
    
    "production": {
        "azure": {
            "openai": {
                "endpoint": "https://prod.openai.azure.com/",
                "api_key": "${AZURE_OPENAI_API_KEY}",
                "deployment_name": "gpt-35-turbo-prod",
                "api_version": "2023-12-01-preview",
                "temperature": 0.3,
                "max_tokens": 2000,
                "timeout": 60
            },
            "speech": {
                "subscription_key": "${AZURE_SPEECH_KEY}",
                "region": "eastus2",
                "language": "en-US"
            }
        },
        "vosk": {
            "model_path": "/opt/vosk/models/vosk-model-en-us-0.22",
            "language": "en"
        },
        "security": {
            "encryption_key": "${ENCRYPTION_KEY}",
            "enable_audit_logging": True,
            "log_level": "INFO"
        },
        "performance": {
            "max_concurrent_transcriptions": 10,
            "transcription_timeout": 300,
            "note_generation_timeout": 120
        }
    }
}

# Invalid configuration examples for testing error handling
INVALID_CONFIGURATIONS = {
    "missing_required_fields": {
        "azure": {
            "openai": {
                "endpoint": "",  # Missing endpoint
                "api_key": "",   # Missing API key
            }
        }
    },
    
    "invalid_urls": {
        "azure": {
            "openai": {
                "endpoint": "not_a_valid_url",
                "api_key": "test_key"
            }
        },
        "ollama": {
            "base_url": "invalid_url_format"
        }
    },
    
    "invalid_types": {
        "azure": {
            "openai": {
                "endpoint": "https://test.openai.azure.com/",
                "api_key": "test_key",
                "temperature": "not_a_number",  # Should be float
                "max_tokens": "invalid"         # Should be int
            }
        },
        "streaming": {
            "max_concurrent_sessions": "fifty",  # Should be int
            "session_timeout_minutes": []        # Should be int
        }
    },
    
    "out_of_range_values": {
        "azure": {
            "openai": {
                "endpoint": "https://test.openai.azure.com/",
                "api_key": "test_key",
                "temperature": 2.5,  # Should be 0-2
                "max_tokens": -100   # Should be positive
            }
        }
    }
}

# Environment variable examples
ENVIRONMENT_VARIABLES = {
    "development": {
        "AZURE_OPENAI_ENDPOINT": "https://dev.openai.azure.com/",
        "AZURE_OPENAI_API_KEY": "dev_key_123",
        "AZURE_OPENAI_DEPLOYMENT": "gpt-35-turbo-dev",
        "AZURE_SPEECH_KEY": "dev_speech_key_456",
        "AZURE_SPEECH_REGION": "westus",
        "VOSK_MODEL_PATH": "/opt/vosk/models/dev",
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "ENCRYPTION_KEY": "dev_encryption_key_789",
        "LOG_LEVEL": "DEBUG"
    },
    
    "testing": {
        "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
        "AZURE_OPENAI_API_KEY": "test_key_123",
        "AZURE_OPENAI_DEPLOYMENT": "gpt-35-turbo-test",
        "AZURE_SPEECH_KEY": "test_speech_key_456",
        "AZURE_SPEECH_REGION": "eastus",
        "VOSK_MODEL_PATH": "/opt/vosk/models/test",
        "ENCRYPTION_KEY": "test_encryption_key_789",
        "LOG_LEVEL": "INFO"
    },
    
    "production": {
        "AZURE_OPENAI_ENDPOINT": "https://prod.openai.azure.com/",
        "AZURE_OPENAI_API_KEY": "prod_key_secure_123",
        "AZURE_OPENAI_DEPLOYMENT": "gpt-35-turbo-prod",
        "AZURE_SPEECH_KEY": "prod_speech_key_secure_456",
        "AZURE_SPEECH_REGION": "eastus2",
        "VOSK_MODEL_PATH": "/opt/vosk/models/prod",
        "OLLAMA_BASE_URL": "http://ollama-service:11434",
        "ENCRYPTION_KEY": "prod_encryption_key_secure_789",
        "LOG_LEVEL": "WARNING"
    }
}

# Configuration file formats for testing
CONFIG_FILE_FORMATS = {
    "yaml": """
azure:
  openai:
    endpoint: "https://test.openai.azure.com/"
    api_key: "test_key_123"
    deployment_name: "gpt-35-turbo"
    api_version: "2023-12-01-preview"
  speech:
    subscription_key: "test_speech_key_456"
    region: "eastus"
    language: "en-US"

vosk:
  model_path: "/opt/vosk/models/vosk-model-en-us-0.22"
  language: "en"

security:
  encryption_key: "test_encryption_key_789"
  enable_audit_logging: true
""",
    
    "json": """{
    "azure": {
        "openai": {
            "endpoint": "https://test.openai.azure.com/",
            "api_key": "test_key_123",
            "deployment_name": "gpt-35-turbo",
            "api_version": "2023-12-01-preview"
        },
        "speech": {
            "subscription_key": "test_speech_key_456",
            "region": "eastus",
            "language": "en-US"
        }
    },
    "vosk": {
        "model_path": "/opt/vosk/models/vosk-model-en-us-0.22",
        "language": "en"
    },
    "security": {
        "encryption_key": "test_encryption_key_789",
        "enable_audit_logging": true
    }
}""",
    
    "toml": """
[azure.openai]
endpoint = "https://test.openai.azure.com/"
api_key = "test_key_123"
deployment_name = "gpt-35-turbo"
api_version = "2023-12-01-preview"

[azure.speech]
subscription_key = "test_speech_key_456"
region = "eastus"
language = "en-US"

[vosk]
model_path = "/opt/vosk/models/vosk-model-en-us-0.22"
language = "en"

[security]
encryption_key = "test_encryption_key_789"
enable_audit_logging = true
"""
}

# .env file examples
ENV_FILE_CONTENTS = {
    "development": """
# Development environment configuration
AZURE_OPENAI_ENDPOINT=https://dev.openai.azure.com/
AZURE_OPENAI_API_KEY=dev_key_123
AZURE_OPENAI_DEPLOYMENT=gpt-35-turbo-dev
AZURE_SPEECH_KEY=dev_speech_key_456
AZURE_SPEECH_REGION=westus
VOSK_MODEL_PATH=/opt/vosk/models/dev
OLLAMA_BASE_URL=http://localhost:11434
ENCRYPTION_KEY=dev_encryption_key_789
LOG_LEVEL=DEBUG
""",
    
    "production": """
# Production environment configuration
AZURE_OPENAI_ENDPOINT=https://prod.openai.azure.com/
AZURE_OPENAI_API_KEY=prod_key_secure_123
AZURE_OPENAI_DEPLOYMENT=gpt-35-turbo-prod
AZURE_SPEECH_KEY=prod_speech_key_secure_456
AZURE_SPEECH_REGION=eastus2
VOSK_MODEL_PATH=/opt/vosk/models/prod
ENCRYPTION_KEY=prod_encryption_key_secure_789
LOG_LEVEL=WARNING
ENABLE_AUDIT_LOGGING=true
MAX_CONCURRENT_SESSIONS=100
"""
}


class ConfigurationFixture:
    """Helper class for creating configuration fixtures."""
    
    def __init__(self):
        self.temp_files = []
    
    def create_config_file(self, content: str, file_format: str = "yaml") -> str:
        """Create a temporary configuration file."""
        suffix = f".{file_format}"
        temp_file = tempfile.NamedTemporaryFile(
            mode='w', 
            suffix=suffix, 
            delete=False,
            encoding='utf-8'
        )
        
        temp_file.write(content)
        temp_file.flush()
        temp_file.close()
        
        self.temp_files.append(temp_file.name)
        return temp_file.name
    
    def create_env_file(self, content: str) -> str:
        """Create a temporary .env file."""
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.env',
            delete=False,
            encoding='utf-8'
        )
        
        temp_file.write(content)
        temp_file.flush()
        temp_file.close()
        
        self.temp_files.append(temp_file.name)
        return temp_file.name
    
    def cleanup(self):
        """Clean up temporary files."""
        for file_path in self.temp_files:
            try:
                os.unlink(file_path)
            except (OSError, FileNotFoundError):
                pass
        self.temp_files.clear()


def get_valid_config(config_type: str = "minimal") -> Dict[str, Any]:
    """Get a valid configuration by type."""
    return VALID_CONFIGURATIONS.get(config_type, VALID_CONFIGURATIONS["minimal"])


def get_invalid_config(error_type: str = "missing_required_fields") -> Dict[str, Any]:
    """Get an invalid configuration by error type."""
    return INVALID_CONFIGURATIONS.get(error_type, INVALID_CONFIGURATIONS["missing_required_fields"])


def get_env_variables(environment: str = "development") -> Dict[str, str]:
    """Get environment variables by environment type."""
    return ENVIRONMENT_VARIABLES.get(environment, ENVIRONMENT_VARIABLES["development"])


def get_config_file_content(file_format: str = "yaml") -> str:
    """Get configuration file content by format."""
    return CONFIG_FILE_FORMATS.get(file_format, CONFIG_FILE_FORMATS["yaml"])


def get_env_file_content(environment: str = "development") -> str:
    """Get .env file content by environment."""
    return ENV_FILE_CONTENTS.get(environment, ENV_FILE_CONTENTS["development"])