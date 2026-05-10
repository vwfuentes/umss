import urllib.request
import json
import os

def text_to_audio(input_file: str, output_file: str, api_key: str = None, model: str = "openai/tts-1") -> str:
    """
    Reads text from a file and generates TTS audio using OpenRouter's OpenAI-compatible speech endpoint.

    Parameters:
        input_file (str): Path to a UTF‑8 text file containing the text to speak.
        output_file (str): Path where the generated WAV audio will be saved.
        api_key (str, optional): OpenRouter API key. If not provided, reads from the
                                  environment variable OPENROUTER_API_KEY.
        model (str, optional): The OpenRouter TTS model identifier.
                                Defaults to "openai/tts-1". Other options: "openai/tts-1-hd".

    Returns:
        str: Path to the created audio file, or None if an error occurred.

    Raises:
        ValueError: If no API key is found or the input file is empty.
    """
    # Use the provided API key or fall back to the OPENROUTER_API_KEY environment variable
    key = api_key or os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise ValueError("OpenRouter API key not found. Set OPENROUTER_API_KEY or pass it as an argument.")

    # Read the entire text file (UTF‑8) and remove surrounding whitespace
    with open(input_file, 'r', encoding='utf-8') as f:
        text_content = f.read().strip()

    # Ensure the file isn't blank
    if not text_content:
        raise ValueError("The input text file is empty.")

    # OpenRouter's speech endpoint (OpenAI‑compatible)
    url = "https://openrouter.ai/api/v1/audio/speech"

    # Payload identical to OpenAI's TTS API
    payload = {
        "model": model,          # OpenRouter model identifier (e.g., "openai/tts-1")
        "input": text_content,   # The text to convert to speech
        "voice": "alloy",        # You can change the voice (alloy, echo, fable, onyx, nova, shimmer)
        "response_format": "wav" # Request WAV binary directly
    }

    # Encode the payload to JSON bytes
    data = json.dumps(payload).encode('utf-8')

    # Headers for OpenRouter – note the additional optional headers for ranking
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {key}',
        # Optional but recommended by OpenRouter:
        # 'HTTP-Referer': 'http://your-site.com',  # or your app's URL
        # 'X-Title': 'Your Application Name'
    }

    # Create the POST request
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        # Send request and read the raw binary audio
        with urllib.request.urlopen(req) as response:
            audio_data = response.read()   # OpenRouter returns the WAV file bytes directly

            # Write the audio bytes to disk
            with open(output_file, 'wb') as wav_file:
                wav_file.write(audio_data)

            print(f"Audio successfully generated and saved to {output_file}")
            return output_file

    except Exception as e:
        print(f"Failed to generate audio: {e}")
        return None