"""
config.py
Central configuration + logging bootstrap
"""

from __future__ import annotations
import os, logging
from pathlib import Path
from dotenv import load_dotenv

# ───────────────────────────── load .env
load_dotenv()

# ───────────────────────────── configuration dict
config: dict[str, object] = {
    # Azure credentials
    "AZURE_API_KEY": os.getenv("AZURE_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY"),
    "AZURE_ENDPOINT": os.getenv(
        "AZURE_ENDPOINT", "https://spd-prod-openai-va-apim.azure-api.us/api"),
    "MODEL_NAME":   os.getenv("MODEL_NAME", "gpt-4o"),
    "API_VERSION":  os.getenv("API_VERSION", "2024-02-15-preview"),

    # Azure Speech credentials
    "AZURE_SPEECH_API_KEY": os.getenv("AZURE_SPEECH_API_KEY"),
    "AZURE_SPEECH_ENDPOINT": os.getenv("AZURE_SPEECH_ENDPOINT"),

    # fallback local model server
    "LOCAL_MODEL_API_URL": os.getenv(
        "LOCAL_MODEL_API_URL", "http://localhost:8000/generate_note"),

    # debug
    "DEBUG_MODE": os.getenv("DEBUG_MODE", "False").lower() == "true",

    # audio defaults
    "CHUNK":      1024,
    "FORMAT_STR": "paInt16",   # 16-bit PCM
    "CHANNELS":   1,
    "RATE":       16000,

    # base filesystem layout
    "BASE_DIR":           Path("./app_data"),
    "LOCAL_MODELS_DIR":   Path("./local_llm_models"),

    # Whisper open-source settings
    "USE_WHISPER":        os.getenv("USE_WHISPER", "False").lower() == "true",
    "WHISPER_MODEL_SIZE": os.getenv("WHISPER_MODEL_SIZE", "tiny"),
    "WHISPER_MODELS_DIR": Path("./app_data/whisper_models"),
    "WHISPER_DEVICE":     "cpu",
}

# derive sub-dirs
config["MODEL_DIR"]  = config["BASE_DIR"] / "models"
config["KEY_DIR"]    = config["BASE_DIR"] / "keys"
config["LOG_DIR"]    = config["BASE_DIR"] / "logs"
config["CACHE_DIR"]  = config["BASE_DIR"] / "cache"
config["NOTES_DIR"]  = config["BASE_DIR"] / "notes"
config["PROMPT_STORE"] = config["BASE_DIR"] / "prompt_templates.json"

# bundled FFmpeg path
if os.name == "nt":
    config["FFMPEG_PATH"] = Path(
        "./ffmpeg/bin/ffmpeg.exe")
else:
    config["FFMPEG_PATH"] = Path(
        "./ffmpeg/bin/ffmpeg")

# ensure directories exist
for d in (
    config["MODEL_DIR"], config["KEY_DIR"], config["LOG_DIR"],
    config["CACHE_DIR"], config["NOTES_DIR"], config["WHISPER_MODELS_DIR"]
):
    Path(d).mkdir(parents=True, exist_ok=True)

# ───────────────────────────── logging
log_level = logging.DEBUG if config["DEBUG_MODE"] else logging.INFO
logging.basicConfig(
    filename=config["LOG_DIR"] / "app.log",
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ambient_scribe")
logger.info("Configuration loaded.")

# ───────────────────────────── expose key paths for "from config import MODEL_DIR"
MODEL_DIR            = config["MODEL_DIR"]
KEY_DIR              = config["KEY_DIR"]
LOG_DIR              = config["LOG_DIR"]
CACHE_DIR            = config["CACHE_DIR"]
NOTES_DIR            = config["NOTES_DIR"]
WHISPER_MODELS_DIR   = config["WHISPER_MODELS_DIR"]
