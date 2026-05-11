import urllib.request
import urllib.error
import json
import os
import base64
import wave
import tempfile
import threading

# pyaudio is only needed for microphone recording
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False

# ── Microphone settings ────────────────────────────────────────────────────
MIC_SAMPLE_RATE = 16000   # Hz  — good for speech
MIC_CHANNELS    = 1       # mono
MIC_CHUNK       = 1024    # frames per buffer
MIC_MAX_SECONDS = 60      # safety cap

SUPPORTED_FORMATS = (".mp3", ".wav", ".ogg", ".flac", ".m4a", ".webm")


# ── Internal: record from microphone ──────────────────────────────────────

def _record_from_microphone(max_seconds: int = MIC_MAX_SECONDS) -> str:
    """
    Records from the default microphone until the user presses Enter.
    Saves to a temp WAV file and returns its path.
    """
    if not PYAUDIO_AVAILABLE:
        raise ImportError(
            "pyaudio is required for microphone input.\n"
            "  Ubuntu/Debian : sudo apt-get install portaudio19-dev && pip install pyaudio\n"
            "  macOS         : brew install portaudio && pip install pyaudio\n"
            "  Windows       : pip install pyaudio"
        )

    pa         = pyaudio.PyAudio()
    frames     = []
    stop_event = threading.Event()

    def _wait_for_enter():
        input()          # blocks until Enter is pressed
        stop_event.set()

    stream = pa.open(
        format=pyaudio.paInt16,
        channels=MIC_CHANNELS,
        rate=MIC_SAMPLE_RATE,
        input=True,
        frames_per_buffer=MIC_CHUNK,
    )

    print("[STT] 🎙️  Recording... Press Enter to stop.")
    threading.Thread(target=_wait_for_enter, daemon=True).start()

    max_chunks = int(MIC_SAMPLE_RATE / MIC_CHUNK * max_seconds)
    for _ in range(max_chunks):
        if stop_event.is_set():
            break
        frames.append(stream.read(MIC_CHUNK, exception_on_overflow=False))

    stream.stop_stream()
    stream.close()
    pa.terminate()
    print("[STT] ⏹️  Recording stopped.")

    # Write frames to a temp WAV file
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    with wave.open(tmp.name, "wb") as wf:
        wf.setnchannels(MIC_CHANNELS)
        wf.setsampwidth(pa.get_sample_size(pyaudio.paInt16))
        wf.setframerate(MIC_SAMPLE_RATE)
        wf.writeframes(b"".join(frames))

    duration = len(frames) * MIC_CHUNK / MIC_SAMPLE_RATE
    print(f"[STT] Captured {duration:.1f}s of audio.")
    return tmp.name


# ── Internal: send audio file to OpenRouter ───────────────────────────────

def _transcribe_with_openrouter(
    audio_path: str,
    api_key: str,
    model: str,
    language_hint: str = None,
) -> str:
    ext = os.path.splitext(audio_path)[1].lower()
    if ext not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported format '{ext}'. Supported: {', '.join(SUPPORTED_FORMATS)}"
        )

    print(f"[STT] Encoding '{os.path.basename(audio_path)}'...")
    with open(audio_path, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode("utf-8")

    hint   = f" The audio is in {language_hint}." if language_hint else ""
    prompt = (
        "Transcribe the following audio exactly as spoken, "
        "preserving punctuation and natural phrasing."
        + hint
        + " Return ONLY the transcription, nothing else."
    )

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data":   audio_b64,
                            "format": ext.lstrip("."),  # e.g. "wav", "mp3"
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    }

    data    = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type":  "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=data, headers=headers, method="POST",
    )

    print(f"[STT] Sending to OpenRouter ({model})...")
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenRouter HTTP {e.code}: {body}") from e
    except Exception as e:
        raise RuntimeError(f"Request failed: {e}") from e

    try:
        return result["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Unexpected response format: {result}") from e


# ── Public function ───────────────────────────────────────────────────────

def stt(
    audio_file: str = None,
    output_file: str = None,
    language_hint: str = None,
    api_key: str = None,
    model: str = "openai/gpt-4o-audio-preview",
    max_record_seconds: int = MIC_MAX_SECONDS,
) -> str:
    """
    Speech-to-Text via OpenRouter.

    Two modes:
      • audio_file="path/to/file.mp3"  → transcribes the given file
      • audio_file=None                → records from the microphone

    Args:
        audio_file:          Path to audio file, or None to use the microphone.
        output_file:         Optional path to save the transcription as .txt.
        language_hint:       Optional language hint e.g. "Spanish", "English".
        api_key:             OpenRouter API key (falls back to OPENROUTER_API_KEY).
        model:               OpenRouter model that supports audio input.
        max_record_seconds:  Max mic recording time in seconds (default 60).

    Returns:
        Transcribed text as a string.

    Raises:
        FileNotFoundError : audio_file path does not exist.
        ValueError        : missing API key or unsupported audio format.
        RuntimeError      : OpenRouter API call failed.
        ImportError       : microphone requested but pyaudio not installed.
    """
    key = api_key or os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise ValueError(
            "API key not found. Set OPENROUTER_API_KEY or pass api_key='sk-or-...'"
        )

    temp_path = None

    try:
        if audio_file:
            # ── Mode 1: file path ──────────────────────────────────────
            if not os.path.isfile(audio_file):
                raise FileNotFoundError(f"Audio file not found: '{audio_file}'")
            print(f"[STT] Using file: '{audio_file}'")
            source_path = audio_file
        else:
            # ── Mode 2: microphone ─────────────────────────────────────
            source_path = _record_from_microphone(max_seconds=max_record_seconds)
            temp_path   = source_path   # mark for cleanup

        transcription = _transcribe_with_openrouter(
            audio_path=source_path,
            api_key=key,
            model=model,
            language_hint=language_hint,
        )

    finally:
        # Clean up the temp recording file if one was created
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

    print(f"[STT] ✅ Transcription complete ({len(transcription)} chars).")

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(transcription)
        print(f"[STT] Saved to '{output_file}'.")

    return transcription


# ── CLI ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # python stt.py audio.mp3
        result = stt(audio_file=sys.argv[1], output_file="transcription.txt")
    else:
        # python stt.py   ← records from microphone
        result = stt(output_file="transcription.txt")

    print("\n--- Transcription ---")
    print(result)