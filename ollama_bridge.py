# Simple API bridge for Ollama to use with the transcription app
from flask import Flask, request, jsonify
import requests
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ollama_bridge")

app = Flask(__name__)

# Model name mapping (Windows filename to Ollama model name)
MODEL_MAPPING = {
    "gemma3-4b": "gemma3:4b",
    "deepseek-r1-14b": "deepseek-r1:14b",
    "llama3": "llama3:latest",
    "phi4": "phi4:latest"
}

def _process_request(default_system_message: str, response_key: str):
    """Generic request handler for Ollama."""
    try:
        data = request.json
        prompt = data.get('prompt', '')
        system_prompt = data.get('system_prompt') # Get agent-provided system prompt
        is_json_output = data.get('is_json_output', False)

        # Get model name from request
        requested_model = data.get('model', 'gemma3-4b')

        # Map directory name to Ollama model name
        if requested_model in MODEL_MAPPING:
            model = MODEL_MAPPING[requested_model]
        else:
            # Try to convert hyphens to colons as fallback
            model = requested_model.replace('-', ':')
            logger.info(f"Model mapping not found, converted {requested_model} to {model}")

        logger.info(f"Received model name: {requested_model}, using Ollama model: {model}")

        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400

        # Use agent's system prompt if available, otherwise use the default
        system_message = system_prompt or default_system_message

        # Prepare payload for Ollama
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system_message,
            "stream": False
        }
        if is_json_output:
            payload["format"] = "json"
            logger.info("Requesting JSON format from Ollama.")

        # Call Ollama API
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=120
        )

        if response.status_code != 200:
            logger.error(f"Ollama API error: {response.status_code} - {response.text}")
            return jsonify({"error": f"Ollama API error: {response.status_code}"}), 500

        result = response.json()
        content = result.get('response', '')

        return jsonify({response_key: content})

    except requests.exceptions.Timeout:
        logger.error("Timeout while waiting for Ollama API response")
        return jsonify({"error": "Ollama API timeout - model may be taking too long"}), 504

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/generate_note', methods=['POST'])
def generate_note():
    """Generate a note using Ollama API."""
    default_system_message = (
        "You are a medical transcription assistant specialized in formatting "
        "medical notes based on transcribed audio. Format the transcription into "
        "a proper medical note according to the instructions."
    )
    return _process_request(
        default_system_message=default_system_message,
        response_key="note"
    )

@app.route('/cleanup_transcription', methods=['POST'])
def cleanup_transcription():
    """Clean up a medical transcription using Ollama API."""
    default_system_message = (
        "You are a medical transcription assistant specialized in cleaning up "
        "and correcting raw medical transcriptions. Fix spelling errors, "
        "improve punctuation, correct medical terminology, and highlight "
        "important medical terms. Stay faithful to the original content, "
        "making only necessary corrections."
    )
    return _process_request(
        default_system_message=default_system_message,
        response_key="cleaned_text"
    )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8001))
    logger.info(f"Starting Ollama API bridge on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)