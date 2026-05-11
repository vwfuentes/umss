import speech_recognition as sr


def stt(
    output_file: str = None,
    language: str = "en-US",
    timeout: int = 5,
    phrase_limit: int = 30,
) -> str:
    """
    Records from the microphone and transcribes using Google's free STT.
    No API key or balance required.

    Args:
        output_file:  Optional path to save the transcription as .txt.
        language:     Language code e.g. "en-US", "es-ES", "fr-FR" (default "en-US").
        timeout:      Seconds to wait for speech to start before giving up (default 5).
        phrase_limit: Max seconds to record a single phrase (default 30).

    Returns:
        Transcribed text as a string.

    Raises:
        RuntimeError: If no speech was detected or transcription failed.
    """
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("[STT] 🎙️  Adjusting for ambient noise...")
        recognizer.adjust_for_ambient_noise(source, duration=1)

        print("[STT] 🎙️  Listening... Speak now.")
        try:
            audio = recognizer.listen(
                source,
                timeout=timeout,
                phrase_time_limit=phrase_limit,
            )
        except sr.WaitTimeoutError:
            raise RuntimeError(
                "No speech detected within the timeout period. Please try again."
            )

    print("[STT] ⏹️  Audio captured. Transcribing...")

    try:
        transcription = recognizer.recognize_google(audio, language=language)
    except sr.UnknownValueError:
        raise RuntimeError("Could not understand the audio. Please speak more clearly.")
    except sr.RequestError as e:
        raise RuntimeError(f"Google STT request failed: {e}")

    print(f"[STT] ✅ Transcription complete ({len(transcription)} chars).")

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(transcription)
        print(f"[STT] Saved to '{output_file}'.")

    return transcription


# ── CLI ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    result = stt(output_file="transcription.txt")
    print("\n--- Transcription ---")
    print(result)