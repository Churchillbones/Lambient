#!/usr/bin/env python3
"""Direct test of Vosk transcription to debug issues."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_vosk_direct():
    """Test Vosk transcription directly."""
    from src.asr.vosk import VoskTranscriber
    
    model_path = Path("app_data/models/vosk-model-en-us-0.22")
    
    print(f"Testing Vosk with model: {model_path}")
    print(f"Model exists: {model_path.exists()}")
    
    if not model_path.exists():
        print("ERROR: Model directory not found!")
        return
    
    # List model contents
    print(f"Model contents: {list(model_path.iterdir())}")
    
    transcriber = VoskTranscriber(model_path=model_path)
    
    # Test with a dummy WAV file (you'll need to provide a real one)
    test_wav = Path("test_audio.wav")  # Replace with actual test file
    
    if test_wav.exists():
        print(f"Testing with audio file: {test_wav}")
        result = transcriber.transcribe(test_wav)
        print(f"Transcription result: '{result}'")
    else:
        print(f"No test audio file found at {test_wav}")
        print("Create a test WAV file or update the path in this script")

if __name__ == "__main__":
    test_vosk_direct() 