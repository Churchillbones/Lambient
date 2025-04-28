"""
transcription.py
Adaptive ASR pipeline with support for Azure Whisper, dynamic local Whisper sizes (tiny/base/medium), and Vosk.
"""
from __future__ import annotations
import os, json, io, tarfile, requests, sys, subprocess
from pathlib import Path
from typing import Literal, Union, Optional

from .config import config, MODEL_DIR, logger

# Set FFmpeg path in environment variables
ffmpeg_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "ffmpeg", "bin"))
os.environ["PATH"] = os.environ["PATH"] + os.pathsep + ffmpeg_path
logger.info(f"Added FFmpeg path to environment: {ffmpeg_path}")

# Verify FFmpeg is available
def verify_ffmpeg():
    try:
        # Use the specific ffmpeg path in the provided directory
        ffmpeg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ffmpeg", "bin", "ffmpeg.exe")
        
        # Check if the ffmpeg executable exists at the specified path
        if not os.path.exists(ffmpeg_path):
            logger.error(f"FFmpeg not found at expected path: {ffmpeg_path}")
            return False

        # Try to run ffmpeg -version to check if it's available
        subprocess.run(
            [ffmpeg_path, "-version"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            check=True
        )
        logger.info(f"FFmpeg verified successfully at {ffmpeg_path}")
        return True
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        logger.error(f"FFmpeg check failed: {e}")
        return False

# Check FFmpeg availability at module import time
ffmpeg_available = verify_ffmpeg()

# Helper function to download Whisper models
def _download_whisper_model(model_size: str, custom_dir: Path) -> None:
    """Download a Whisper model to our custom directory"""
    import whisper
    
    # Create the directory if it doesn't exist
    custom_dir.mkdir(parents=True, exist_ok=True)
    
    # Use whisper's download mechanism but redirect to our custom directory
    logger.info(f"Downloading Whisper {model_size} model to {custom_dir}...")
    try:
        # Temporarily change the _MODELS_DIR to our custom directory
        original_models_dir = whisper._MODELS_DIR
        whisper._MODELS_DIR = str(custom_dir)
        
        # Force download by trying to load the model
        whisper.load_model(model_size, download_root=str(custom_dir))
        
        # Restore the original models directory
        whisper._MODELS_DIR = original_models_dir
        
        logger.info(f"Successfully downloaded Whisper {model_size} model")
    except Exception as e:
        logger.error(f"Failed to download Whisper model: {e}")
        raise

# Dynamic Whisper back-end helper
def _local_whisper_dynamic(wav: Path, size: str) -> str:
    import whisper  # pip install -U openai-whisper
    
    # Verify FFmpeg is available
    if not ffmpeg_available:
        return "ERROR: FFmpeg not found. Please ensure FFmpeg is properly installed."
    
    try:
        # Get the custom model directory
        custom_model_dir = Path(config.get("WHISPER_MODELS_DIR", "app_data/whisper_models"))
        custom_model_dir.mkdir(parents=True, exist_ok=True)
        model_path = custom_model_dir / f"{size}.pt"
        
        # If model doesn't exist, try to download it
        if not model_path.exists():
            logger.info(f"Whisper model {size} not found. Attempting to download...")
            try:
                _download_whisper_model(size, custom_model_dir)
            except Exception as e:
                logger.error(f"Could not download model: {e}")
                pass  # Continue with default paths if download fails
        
        # Try to load from custom directory first
        if model_path.exists():
            logger.info(f"Loading Whisper model from custom path: {model_path}")
            model = whisper.load_model(size, download_root=str(custom_model_dir))
        else:
            # Fall back to default location with auto-download
            logger.warning(f"Using default whisper model location for {size}")
            model = whisper.load_model(size)
            
        # Run transcription with explicit language setting
        result = model.transcribe(str(wav), language="en")
        return result.get("text", "")
    except Exception as e:
        logger.error(f"Local Whisper recognition failed (size={size}): {e}")
        return f"ERROR: Whisper transcription failed: {e}"

# Vosk back-end

def _vosk_small(wav: Path) -> str:
    try:
        from vosk import Model, KaldiRecognizer
    except ImportError:
        return "ERROR: 'vosk' not installed."
    model_dir = MODEL_DIR / "vosk-model-small-en-us-0.15"
    if not model_dir.exists():
        _download_vosk(model_dir)
    rec = KaldiRecognizer(Model(str(model_dir)), config["RATE"])
    with open(wav, "rb") as fh:
        while True:
            data = fh.read(4000)
            if not data:
                break
            rec.AcceptWaveform(data)
    final = json.loads(rec.FinalResult())
    return final.get("text", "")

# Azure Whisper

def _azure_whisper(wav: Path) -> str:
    from openai import AzureOpenAI  # pip install openai
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    )
    with open(wav, "rb") as fh:
        resp = client.audio.transcriptions.create(
            model="whisper-1",
            file=fh,
            response_format="text",
            language="en",
        )
    return resp

# Download Vosk model if missing

def _download_vosk(target: Path) -> None:
    url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
    logger.info("Downloading Vosk model (~50 MB)…")
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    with tarfile.open(fileobj=io.BytesIO(r.content), mode="r:gz") as tar:
        tar.extractall(target.parent)

def _azure_speech(wav_path: Path, api_key: str, endpoint: str) -> str:
    """Transcribe audio using Azure Speech API with 45-second chunking."""
    import wave
    import requests
    import math
    
    try:
        # Open the WAV file and get its properties
        with wave.open(str(wav_path), 'rb') as wf:
            channels = wf.getnchannels()
            framerate = wf.getframerate()
            sample_width = wf.getsampwidth()
            n_frames = wf.getnframes()
            
            # Calculate chunk size for 45 seconds
            frames_per_chunk = int(framerate * 45)
            n_chunks = math.ceil(n_frames / frames_per_chunk)
            
            full_transcript = []
            
            # Process each 45-second chunk
            for i in range(n_chunks):
                # Read chunk of frames
                start_frame = i * frames_per_chunk
                wf.setpos(start_frame)
                chunk_frames = wf.readframes(frames_per_chunk)
                
                # Create a temporary WAV file in memory for this chunk
                chunk_wav = io.BytesIO()
                with wave.open(chunk_wav, 'wb') as chunk_wf:
                    chunk_wf.setnchannels(channels)
                    chunk_wf.setsampwidth(sample_width)
                    chunk_wf.setframerate(framerate)
                    chunk_wf.writeframes(chunk_frames)
                
                # Prepare the request
                request_url = f"{endpoint}/speech/recognition/conversation/cognitiveservices/v1"
                headers = {
                    'api-key': api_key,
                    'Content-Type': 'audio/wav'
                }
                
                # Send request to Azure
                response = requests.post(
                    request_url,
                    headers=headers,
                    data=chunk_wav.getvalue()
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("RecognitionStatus") == "Success":
                        text = result.get("DisplayText", "").strip()
                        if text:
                            full_transcript.append(text)
                else:
                    logger.error(f"Azure Speech API error on chunk {i}: {response.status_code} - {response.text}")
                    
        return " ".join(full_transcript)
        
    except Exception as e:
        logger.error(f"Error in Azure Speech transcription: {e}", exc_info=True)
        return f"ERROR: Azure Speech transcription failed: {str(e)}"

# Main entry: choose ASR backend

def transcribe_audio(
    audio_path: Union[str, Path],
    model: str,
    model_path: Optional[str] = None,
    azure_key: Optional[str] = None,
    azure_endpoint: Optional[str] = None
) -> str:
    """
    Transcribe audio using specified model.

    model can be:
    - 'azure_speech'
    - 'azure_whisper'
    - 'vosk_small'
    - 'vosk_model' (requires model_path to be provided)
    - 'local_whisper' (uses base model)
    - 'whisper:tiny', 'whisper:base', 'whisper:medium' for dynamic local Whisper
    """
    wav = Path(audio_path)
    model_str = model.lower()

    # Dynamic local Whisper sizes
    if model_str.startswith("whisper:"):
        size = model_str.split(":", 1)[1]
        return _local_whisper_dynamic(wav, size)

    if model_str == "azure_whisper":
        return _azure_whisper(wav)
        
    if model_str == "azure_speech":
        if not azure_key or not azure_endpoint:
            return "ERROR: Azure Speech requires API key and endpoint"
        return _azure_speech(wav, azure_key, azure_endpoint)

    if model_str == "local_whisper":
        # Fallback to base model
        return _local_whisper_dynamic(wav, config.get("WHISPER_MODEL_SIZE", "base"))

    if model_str == "vosk_small":
        return _vosk_small(wav)
        
    if model_str == "vosk_model" and model_path:
        try:
            from vosk import Model, KaldiRecognizer
        except ImportError:
            return "ERROR: 'vosk' not installed."
            
        try:
            model_dir = Path(model_path)
            if not model_dir.exists():
                logger.error(f"Specified Vosk model path does not exist: {model_path}")
                return f"ERROR: Vosk model not found at {model_path}"
                
            rec = KaldiRecognizer(Model(str(model_dir)), config["RATE"])
            with open(wav, "rb") as fh:
                while True:
                    data = fh.read(4000)
                    if not data:
                        break
                    rec.AcceptWaveform(data)
            final = json.loads(rec.FinalResult())
            return final.get("text", "")
        except Exception as e:
            logger.error(f"Error using custom Vosk model: {e}")
            return f"ERROR: Failed to use custom Vosk model: {e}"

    return f"ERROR: Unknown ASR model '{model}'."
repr("")