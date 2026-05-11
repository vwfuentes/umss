import urllib.request
import urllib.error
import json
import os
import wave
import struct

def text_to_audio(input_file: str, output_file: str, api_key: str = None, model: str = "openai/gpt-4o-mini-tts-2025-12-15") -> str:
    """
    Converts text in a file to WAV audio using OpenRouter's TTS endpoint.

    Because OpenRouter only supports 'mp3' or 'pcm' format, we request raw PCM
    and build a WAV container around it.

    Args:
        input_file (str): Path to UTF‑8 text file containing the text to speak.
        output_file (str): Path where the generated WAV audio will be saved.
        api_key (str, optional): OpenRouter API key. Defaults to env OPENROUTER_API_KEY.
        model (str, optional): OpenRouter TTS model ID. Defaults to "openai/tts-1".

    Returns:
        str: Path to the created WAV file, or None on failure.
    """
    # Use the provided key or read from environment
    key = api_key or os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise ValueError("OpenRouter API key not found. Set OPENROUTER_API_KEY or pass it as an argument.")

    # Read the entire text, stripping extra whitespace
    with open(input_file, 'r', encoding='utf-8') as f:
        text_content = f.read().strip()

    if not text_content:
        raise ValueError("The input text file is empty.")

    url = "https://openrouter.ai/api/v1/audio/speech"

    # Payload: request raw PCM audio (OpenRouter restricts format to "mp3" or "pcm")
    payload = {
        "model": model,
        "input": text_content,
        "voice": "alloy",
        "response_format": "pcm"       # OpenRouter accepts "mp3" or "pcm"
    }

    data = json.dumps(payload).encode('utf-8')

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {key}',
        'HTTP-Referer': 'http://localhost:8000',  # replace with your site
        'X-Title': 'GrammarTTS Pipeline'
    }

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req) as response:
            pcm_data = response.read()          # raw 16-bit PCM audio bytes

            # PCM from OpenAI/OpenRouter is 24 kHz mono 16-bit little-endian
            sample_rate = 24000
            num_channels = 1
            sample_width = 2                    # 16 bits = 2 bytes

            # Build a WAV file from the PCM data
            with wave.open(output_file, 'wb') as wav_file:
                wav_file.setnchannels(num_channels)
                wav_file.setsampwidth(sample_width)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(pcm_data)

            print(f"✅ Audio successfully saved to {output_file}")
            return output_file

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"❌ HTTP Error {e.code}: {e.reason}")
        print("OpenRouter response:", error_body)
        return None
    except Exception as e:
        print(f"❌ Failed to generate audio: {e}")
        return None