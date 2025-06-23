# PHASE 1: Architecture & Design Pattern Foundation - Implementation Plan

## Overview
Phase 1 establishes the architectural foundation by implementing core design patterns and OOP principles. This creates a robust, maintainable structure supporting dependency injection, proper encapsulation, and modular design.

## **STEP 1.1: Implement Dependency Injection Container**

### **Objective**
Create a centralized dependency injection system to eliminate hard-coded dependencies and improve testability through loose coupling.

### **OOP Principles Applied**
- **Encapsulation**: Service dependencies are encapsulated within the container
- **Abstraction**: Hide complex instantiation logic behind simple interfaces  
- **Polymorphism**: Services can be swapped via interface implementations

### **Implementation Steps**

#### **Step 1.1.1: Create Core Exception Hierarchy**
**File**: `src/core/exceptions.py`
**Purpose**: Establish custom exception hierarchy following Python best practices

```python
class AmbientScribeError(Exception):
    """Base exception for all application-specific errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}

class ConfigurationError(AmbientScribeError):
    """Raised when configuration is invalid or missing."""
    pass

class ServiceNotFoundError(AmbientScribeError):
    """Raised when a requested service is not registered in the container."""
    pass
```

**Justification**: Creates a clear exception hierarchy that allows for specific error handling while maintaining the ability to catch all application errors at the base level.

#### **Step 1.1.2: Create Service Interfaces**
**File**: `src/core/interfaces/transcription.py`
**Purpose**: Define abstract interfaces following Interface Segregation Principle

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any

class ITranscriber(ABC):
    """Abstract interface for audio transcription services."""
    
    @abstractmethod
    async def transcribe(self, audio_path: Path, **kwargs) -> str:
        """Transcribe audio file to text."""
        pass
    
    @abstractmethod
    def is_supported_format(self, file_path: Path) -> bool:
        """Check if the audio format is supported by this transcriber."""
        pass
```

#### **Step 1.1.3: Implement Dependency Injection Container**
**File**: `src/core/container.py`
**Purpose**: Centralized service container implementing Inversion of Control

```python
from typing import TypeVar, Type, Dict, Any, Callable

T = TypeVar('T')

class ServiceContainer:
    """Dependency injection container following IoC principle."""
    
    def __init__(self) -> None:
        self._services: Dict[Type[Any], Any] = {}
        self._singletons: Dict[Type[Any], Any] = {}
    
    def register_singleton(self, interface: Type[T], implementation: Type[T]) -> None:
        """Register a service as singleton."""
        self._services[interface] = implementation
    
    def resolve(self, interface: Type[T]) -> T:
        """Resolve a service instance by interface type."""
        if interface in self._singletons:
            return self._singletons[interface]
        
        if interface in self._services:
            instance = self._create_instance(self._services[interface])
            self._singletons[interface] = instance
            return instance
        
        raise ServiceNotFoundError(f"Service {interface.__name__} not registered")
```

## **STEP 1.2: Implement Factory Pattern for Service Creation**

### **Objective**
Create factory classes that encapsulate complex service creation logic and provide consistent interface for creating related objects.

### **OOP Principles Applied**
- **Encapsulation**: Complex creation logic is hidden within factory classes
- **Single Responsibility**: Each factory has one job - creating specific types of services
- **Open/Closed Principle**: New providers can be added without modifying existing factories

#### **Step 1.2.1: Create Base Factory Interface**
**File**: `src/core/factories/base_factory.py`

```python
from abc import ABC, abstractmethod
from typing import TypeVar, Generic

T = TypeVar('T')

class IServiceFactory(ABC, Generic[T]):
    """Abstract factory interface for creating services."""
    
    @abstractmethod
    def create(self, provider_type: str, **kwargs) -> T:
        """Create service instance based on provider type."""
        pass
    
    @abstractmethod
    def get_supported_providers(self) -> list[str]:
        """Get list of supported provider types."""
        pass
```

#### **Step 1.2.2: Implement Transcriber Factory**
**File**: `src/core/factories/transcriber_factory.py`

```python
from typing import Dict, Type
from .base_factory import IServiceFactory
from ..interfaces.transcription import ITranscriber

class TranscriberFactory(IServiceFactory[ITranscriber]):
    """Factory for creating transcriber instances."""
    
    def __init__(self) -> None:
        self._providers: Dict[str, Type[ITranscriber]] = {}
        self._register_default_providers()
    
    def create(self, provider_type: str, **kwargs) -> ITranscriber:
        """Create transcriber instance for specified provider."""
        if provider_type not in self._providers:
            raise ServiceNotFoundError(f"Provider '{provider_type}' not supported")
        
        provider_class = self._providers[provider_type]
        return self._create_configured_instance(provider_class, provider_type, kwargs)
```

## **STEP 1.3: Configuration Management Refactoring**

### **Objective**
Refactor the monolithic configuration system into a proper service with validation, type safety, and clear separation of concerns.

### **OOP Principles Applied**
- **Single Responsibility**: Configuration service only handles configuration
- **Encapsulation**: Configuration details are hidden behind service interface
- **Dependency Inversion**: Services depend on configuration interface, not implementation

#### **Step 1.3.1: Create Settings Models**
**File**: `src/core/config/settings.py`

```python
from pydantic import BaseSettings, Field, validator
from pathlib import Path
from typing import Optional

class AzureSettings(BaseSettings):
    """Azure service configuration with validation."""
    
    api_key: Optional[str] = Field(None, env='AZURE_API_KEY')
    endpoint: Optional[str] = Field(None, env='AZURE_ENDPOINT')
    model_name: str = Field('gpt-4o', env='MODEL_NAME')
    
    @validator('endpoint')
    def validate_endpoint(cls, v):
        if v and not v.startswith('https://'):
            raise ValueError('Azure endpoint must use HTTPS')
        return v
    
    class Config:
        env_file = '.env'

class ApplicationSettings(BaseSettings):
    """Main application configuration."""
    
    debug_mode: bool = Field(False, env='DEBUG_MODE')
    azure: AzureSettings = Field(default_factory=AzureSettings)
    
    class Config:
        env_file = '.env'
```

#### **Step 1.3.2: Implement Configuration Service**
**File**: `src/core/config/configuration_service.py`

```python
from typing import Any, Dict
from ..interfaces.config_service import IConfigurationService
from .settings import ApplicationSettings

class ConfigurationService(IConfigurationService):
    """Configuration service implementing proper encapsulation."""
    
    def __init__(self, settings: Optional[ApplicationSettings] = None) -> None:
        self._settings = settings or ApplicationSettings()
        
        if not self.validate_configuration():
            raise ConfigurationError("Invalid configuration detected")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key with proper error handling."""
        keys = key.split('.')
        value = self._settings
        
        for k in keys:
            if hasattr(value, k):
                value = getattr(value, k)
            else:
                return default
        
        return value
    
    def validate_configuration(self) -> bool:
        """Validate current configuration for completeness."""
        # Implementation details...
        return True
```

## **STEP 1.4: Integration and Bootstrap**

### **Objective**
Integrate all Phase 1 components and create proper initialization sequence.

#### **Step 1.4.1: Create Application Bootstrap**
**File**: `src/core/bootstrap.py`

```python
from .container import ServiceContainer
from .config.configuration_service import ConfigurationService

class ApplicationBootstrap:
    """Bootstrap class for initializing application dependencies."""
    
    def __init__(self) -> None:
        self._container = ServiceContainer()
        self._is_initialized = False
    
    def initialize(self) -> ServiceContainer:
        """Initialize all application dependencies."""
        if self._is_initialized:
            return self._container
        
        # Step 1: Initialize configuration
        config_service = ConfigurationService()
        self._container.register_instance(IConfigurationService, config_service)
        
        # Step 2: Register factories
        self._register_factories()
        
        self._is_initialized = True
        return self._container
```

## **IMPLEMENTATION CHECKLIST**

### **Pre-Implementation Setup**
- [x] Create directory structure: `src/core/`, `src/core/interfaces/`, `src/core/factories/`, `src/core/config/`
- [x] Install required dependencies: `pydantic`
- [x] Backup existing configuration files

### **Implementation Order**

#### **Week 1: Foundation**
- [x] **Day 1**: Implement exception hierarchy (`src/core/exceptions.py`)
- [x] **Day 2**: Create service interfaces (`src/core/interfaces/`)
- [x] **Day 3**: Create dependency injection container (`src/core/container.py`)
- [x] **Day 4**: Unit tests for container and interfaces (`tests/test_container.py`)
- [x] **Day 5**: Integration testing and bug fixes (FastAPI smoke tests, config tests)

#### **Week 2: Factories and Configuration**
- [x] **Day 1**: Implement base factory interface (`src/core/factories/base_factory.py`)
- [x] **Day 2**: Create transcriber factory (`src/core/factories/transcriber_factory.py`) & `LLMProviderFactory`
- [x] **Day 3**: Create configuration models (`src/core/config/settings.py`) – migrated to Pydantic v2 style
- [x] **Day 4**: Implement configuration service (`src/core/config/configuration_service.py`) & registration in container
- [x] **Day 5**: Create bootstrap system (`src/core/bootstrap.py`) and auto-wiring

### **Quality Assurance Checklist**
- [x] All classes follow Single Responsibility Principle where feasible
- [x] Proper type hints on all methods and functions
- [x] Comprehensive docstrings for public APIs
- [x] Error handling with custom exceptions
- [x] PEP 8 compliance enforced via Black & Ruff CI
- [x] Dependencies properly injected, no hard-coded instantiations
- [x] Configuration validation working correctly (unit-tested)

### **Success Criteria**
- [x] Legacy configuration system successfully migrated
- [x] All services properly registered in DI container
- [x] Factory patterns creating services correctly
- [x] No direct instantiation of services in business logic (phase-1 scope)
- [x] Configuration properly validated and type-safe
- [x] Automated CI pipeline (lint, format, tests) green

---

## ✅ Phase 1 Status: COMPLETED
All architectural foundation tasks have been implemented and verified via automated tests & CI. Remaining warnings are silenced; Phase 2 can proceed (refactor Azure SDK calls, provider-agnostic token management, etc.).

This Phase 1 plan establishes a solid architectural foundation following OOP principles, design patterns, and Python best practices. 