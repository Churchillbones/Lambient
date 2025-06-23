"""Audio sample generator for testing."""

import io
import wave
import tempfile
from pathlib import Path
from typing import Tuple, Optional
import numpy as np


class AudioSampleGenerator:
    """Generate audio samples for testing purposes."""
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.temp_files = []
    
    def generate_silence(self, duration: float, amplitude: float = 0.0) -> np.ndarray:
        """Generate silence audio data."""
        num_samples = int(duration * self.sample_rate)
        return np.full(num_samples, amplitude, dtype=np.float32)
    
    def generate_sine_wave(
        self, 
        duration: float, 
        frequency: float = 440.0, 
        amplitude: float = 0.5
    ) -> np.ndarray:
        """Generate sine wave audio data."""
        num_samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, num_samples, False)
        return amplitude * np.sin(2 * np.pi * frequency * t).astype(np.float32)
    
    def generate_noise(
        self, 
        duration: float, 
        amplitude: float = 0.1,
        noise_type: str = "white"
    ) -> np.ndarray:
        """Generate noise audio data."""
        num_samples = int(duration * self.sample_rate)
        
        if noise_type == "white":
            return amplitude * np.random.normal(0, 1, num_samples).astype(np.float32)
        elif noise_type == "pink":
            # Simplified pink noise generation
            white_noise = np.random.normal(0, 1, num_samples)
            # Apply simple low-pass filter for pink noise approximation
            pink_noise = np.convolve(white_noise, [0.1, 0.2, 0.3, 0.2, 0.1], mode='same')
            return amplitude * pink_noise.astype(np.float32)
        else:
            return self.generate_silence(duration)
    
    def generate_speech_like_signal(self, duration: float) -> np.ndarray:
        """Generate speech-like audio signal for testing."""
        num_samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, num_samples, False)
        
        # Combine multiple frequencies to simulate speech formants
        f1 = 600   # First formant
        f2 = 1200  # Second formant
        f3 = 2400  # Third formant
        
        signal = (
            0.4 * np.sin(2 * np.pi * f1 * t) +
            0.3 * np.sin(2 * np.pi * f2 * t) +
            0.2 * np.sin(2 * np.pi * f3 * t) +
            0.1 * np.random.normal(0, 1, num_samples)  # Add noise
        )
        
        # Apply envelope to make it more speech-like
        envelope = np.exp(-t * 2) * (1 + 0.5 * np.sin(10 * t))
        signal = signal * envelope
        
        # Normalize
        signal = signal / np.max(np.abs(signal)) * 0.7
        
        return signal.astype(np.float32)
    
    def create_wav_file(
        self, 
        audio_data: np.ndarray, 
        filename: Optional[str] = None,
        channels: int = 1
    ) -> str:
        """Create a WAV file from audio data."""
        if filename is None:
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            filename = temp_file.name
            temp_file.close()
            self.temp_files.append(filename)
        
        # Convert to 16-bit PCM
        audio_int16 = (audio_data * 32767).astype(np.int16)
        
        with wave.open(filename, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_int16.tobytes())
        
        return filename
    
    def create_wav_bytes(self, audio_data: np.ndarray, channels: int = 1) -> bytes:
        """Create WAV file bytes from audio data."""
        # Convert to 16-bit PCM
        audio_int16 = (audio_data * 32767).astype(np.int16)
        
        # Create WAV file in memory
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_int16.tobytes())
        
        return wav_buffer.getvalue()
    
    def create_medical_conversation_audio(self, duration: float = 30.0) -> str:
        """Create audio that simulates a medical conversation."""
        # Create alternating segments for doctor and patient
        segment_duration = 3.0  # 3-second segments
        num_segments = int(duration / segment_duration)
        
        full_audio = []
        
        for i in range(num_segments):
            if i % 2 == 0:  # Doctor segments (higher pitch)
                segment = self.generate_speech_like_signal(segment_duration)
                # Slightly higher pitch for doctor
                segment = segment * 1.2
            else:  # Patient segments (lower pitch)
                segment = self.generate_speech_like_signal(segment_duration)
                # Slightly lower pitch for patient
                segment = segment * 0.8
            
            # Add short pause between segments
            pause = self.generate_silence(0.5)
            
            full_audio.extend(segment)
            full_audio.extend(pause)
        
        # Convert to numpy array
        full_audio = np.array(full_audio, dtype=np.float32)
        
        # Normalize
        if np.max(np.abs(full_audio)) > 0:
            full_audio = full_audio / np.max(np.abs(full_audio)) * 0.8
        
        return self.create_wav_file(full_audio)
    
    def create_noisy_audio(self, duration: float = 10.0, snr_db: float = 10.0) -> str:
        """Create audio with background noise for testing noise handling."""
        # Generate speech-like signal
        speech = self.generate_speech_like_signal(duration)
        
        # Generate noise
        noise = self.generate_noise(duration, noise_type="white")
        
        # Calculate noise amplitude for desired SNR
        speech_power = np.mean(speech ** 2)
        noise_power = speech_power / (10 ** (snr_db / 10))
        noise_amplitude = np.sqrt(noise_power / np.mean(noise ** 2))
        
        # Combine speech and noise
        noisy_audio = speech + noise_amplitude * noise
        
        # Normalize
        if np.max(np.abs(noisy_audio)) > 0:
            noisy_audio = noisy_audio / np.max(np.abs(noisy_audio)) * 0.8
        
        return self.create_wav_file(noisy_audio)
    
    def create_test_suite_audio_files(self) -> dict:
        """Create a complete suite of test audio files."""
        files = {}
        
        # Short silence for quick tests
        files['silence_short'] = self.create_wav_file(
            self.generate_silence(1.0), 
            filename=None
        )
        
        # Medium length medical conversation
        files['medical_conversation'] = self.create_medical_conversation_audio(30.0)
        
        # Noisy audio for testing noise handling
        files['noisy_audio'] = self.create_noisy_audio(15.0, snr_db=5.0)
        
        # Pure tone for testing frequency response
        files['tone_440hz'] = self.create_wav_file(
            self.generate_sine_wave(5.0, 440.0, 0.5)
        )
        
        # Long audio for performance testing
        files['long_conversation'] = self.create_medical_conversation_audio(120.0)  # 2 minutes
        
        return files
    
    def cleanup(self):
        """Clean up temporary files."""
        for file_path in self.temp_files:
            try:
                Path(file_path).unlink()
            except (OSError, FileNotFoundError):
                pass
        self.temp_files.clear()


# Convenience functions for pytest fixtures
def create_short_audio_sample() -> Tuple[str, AudioSampleGenerator]:
    """Create a short audio sample for testing."""
    generator = AudioSampleGenerator()
    audio_file = generator.create_wav_file(
        generator.generate_speech_like_signal(5.0)
    )
    return audio_file, generator


def create_medical_audio_sample() -> Tuple[str, AudioSampleGenerator]:
    """Create a medical conversation audio sample."""
    generator = AudioSampleGenerator()
    audio_file = generator.create_medical_conversation_audio(30.0)
    return audio_file, generator


def create_noisy_audio_sample() -> Tuple[str, AudioSampleGenerator]:
    """Create a noisy audio sample for testing noise handling."""
    generator = AudioSampleGenerator()
    audio_file = generator.create_noisy_audio(10.0, snr_db=5.0)
    return audio_file, generator


def create_audio_bytes_sample(duration: float = 5.0) -> bytes:
    """Create audio data as bytes for streaming tests."""
    generator = AudioSampleGenerator()
    audio_data = generator.generate_speech_like_signal(duration)
    return generator.create_wav_bytes(audio_data)


# Pre-defined audio patterns for specific tests
AUDIO_PATTERNS = {
    "silent": lambda duration: AudioSampleGenerator().generate_silence(duration),
    "tone_440": lambda duration: AudioSampleGenerator().generate_sine_wave(duration, 440.0),
    "tone_880": lambda duration: AudioSampleGenerator().generate_sine_wave(duration, 880.0),
    "white_noise": lambda duration: AudioSampleGenerator().generate_noise(duration, 0.1, "white"),
    "pink_noise": lambda duration: AudioSampleGenerator().generate_noise(duration, 0.1, "pink"),
    "speech_like": lambda duration: AudioSampleGenerator().generate_speech_like_signal(duration),
}


def get_audio_pattern(pattern_name: str, duration: float = 5.0) -> np.ndarray:
    """Get audio data for a specific pattern."""
    pattern_func = AUDIO_PATTERNS.get(pattern_name)
    if pattern_func is None:
        raise ValueError(f"Unknown audio pattern: {pattern_name}")
    return pattern_func(duration)