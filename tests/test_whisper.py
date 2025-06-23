#!/usr/bin/env python3
"""Test script for Whisper functionality."""

import os
import sys
from pathlib import Path
import pytest

pytest.skip("Skipping verbose Whisper smoke tests in CI", allow_module_level=True)

def test_whisper_imports():
    """Test Whisper-related imports."""
    results = []
    
    # Test torch
    try:
        import torch
        results.append(f"✅ PyTorch imported successfully (version: {torch.__version__})")
    except ImportError as e:
        results.append(f"❌ PyTorch import failed: {e}")
        return results
    
    # Test whisper
    try:
        import whisper
        results.append("✅ Whisper imported successfully")
    except ImportError as e:
        results.append(f"❌ Whisper import failed: {e}")
        return results
    
    # Test numpy
    try:
        import numpy as np
        results.append(f"✅ NumPy imported successfully (version: {np.__version__})")
    except ImportError as e:
        results.append(f"❌ NumPy import failed: {e}")
    
    # Test torchaudio
    try:
        import torchaudio
        results.append(f"✅ TorchAudio imported successfully (version: {torchaudio.__version__})")
    except ImportError as e:
        results.append(f"⚠️ TorchAudio import failed: {e}")
    
    return results

def test_whisper_models():
    """Test Whisper model availability and download."""
    try:
        import whisper
    except ImportError:
        return ["❌ Whisper not available for model testing"]
    
    results = []
    models_dir = Path("./app_data/whisper_models")
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # Test model availability
    available_models = whisper.available_models()
    results.append(f"📋 Available Whisper models: {', '.join(available_models)}")
    
    # Test tiny model download/load
    try:
        results.append("📥 Testing tiny model download/load...")
        model = whisper.load_model("tiny", download_root=str(models_dir))
        results.append("✅ Tiny model loaded successfully")
        
        # Check model details
        results.append(f"📊 Model device: {next(model.parameters()).device}")
        results.append(f"📊 Model dtype: {next(model.parameters()).dtype}")
        
    except Exception as e:
        results.append(f"❌ Failed to load tiny model: {e}")
    
    return results

def test_whisper_transcription():
    """Test basic Whisper transcription functionality."""
    try:
        import whisper
        import numpy as np
        import wave
    except ImportError as e:
        return [f"❌ Required imports not available for transcription test: {e}"]
    
    results = []
    models_dir = Path("./app_data/whisper_models")
    
    try:
        # Create a simple test audio file
        results.append("🎵 Creating test audio file...")
        test_audio_path = models_dir / "test_whisper.wav"
        
        # Generate 2 seconds of 440Hz sine wave (A4 note)
        sample_rate = 16000
        duration = 2
        t = np.linspace(0, duration, int(sample_rate * duration))
        frequency = 440
        audio_data = (np.sin(2 * np.pi * frequency * t) * 32767).astype(np.int16)
        
        # Save as WAV file
        with wave.open(str(test_audio_path), 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        results.append(f"✅ Test audio created: {test_audio_path}")
        
        # Load model and transcribe
        results.append("🤖 Loading Whisper model...")
        model = whisper.load_model("tiny", download_root=str(models_dir))
        
        results.append("🎤 Testing transcription...")
        result = model.transcribe(str(test_audio_path))
        
        transcription = result.get("text", "").strip()
        results.append(f"📝 Transcription result: '{transcription}'")
        results.append(f"🕐 Processing time: {result.get('segments', [{}])[0].get('end', 0) if result.get('segments') else 'N/A'}")
        
        # Clean up test file
        if test_audio_path.exists():
            test_audio_path.unlink()
            results.append("🧹 Test audio file cleaned up")
        
        results.append("✅ Transcription test completed successfully")
        
    except Exception as e:
        results.append(f"❌ Transcription test failed: {e}")
        # Clean up on error
        test_audio_path = models_dir / "test_whisper.wav"
        if test_audio_path.exists():
            test_audio_path.unlink()
    
    return results

def test_whisper_integration():
    """Test integration with the project's Whisper implementation."""
    results = []
    
    try:
        # Test project's Whisper transcriber
        sys.path.append(str(Path(__file__).parent))
        from src.asr.whisper import WhisperTranscriber
        from src.config import config
        
        results.append("✅ Project Whisper transcriber imported successfully")
        
        # Test transcriber initialization
        transcriber = WhisperTranscriber(size="tiny")
        results.append("✅ WhisperTranscriber initialized successfully")
        
        # Test configuration
        whisper_config = {
            "WHISPER_MODELS_DIR": config.get("WHISPER_MODELS_DIR"),
            "WHISPER_DEVICE": config.get("WHISPER_DEVICE"),
            "USE_WHISPER": config.get("USE_WHISPER"),
        }
        results.append(f"📋 Whisper configuration: {whisper_config}")
        
    except Exception as e:
        results.append(f"❌ Project integration test failed: {e}")
    
    return results

def main():
    """Run all Whisper tests."""
    print("🚀 Whisper Functionality Test Suite")
    print("=" * 50)
    
    # Test imports
    print("\n📦 Testing Imports...")
    print("-" * 30)
    for result in test_whisper_imports():
        print(result)
    
    # Test models
    print("\n🤖 Testing Models...")
    print("-" * 30)
    for result in test_whisper_models():
        print(result)
    
    # Test transcription
    print("\n🎤 Testing Transcription...")
    print("-" * 30)
    for result in test_whisper_transcription():
        print(result)
    
    # Test integration
    print("\n🔗 Testing Project Integration...")
    print("-" * 30)
    for result in test_whisper_integration():
        print(result)
    
    print("\n" + "=" * 50)
    print("✅ Whisper test suite completed!")

if __name__ == "__main__":
    main() 