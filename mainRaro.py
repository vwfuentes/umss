import os
import sys
import time
import random

from parseador import interpret_questions
from ia_messenger import ask_openai, back_translate
from text_to_audio import text_to_audio


def with_retry(fn, *args, max_retries=5, base_delay=2.0, **kwargs):
    """
    Calls fn(*args, **kwargs) and retries on rate-limit (429) or
    server errors (500+) using exponential backoff with jitter.
    """
    for attempt in range(max_retries):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            err = str(e)
            is_rate_limit = "429" in err or "rate limit" in err.lower()
            is_server_err = "500" in err or "502" in err or "503" in err

            if (is_rate_limit or is_server_err) and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                print(f"  ⚠️  Hit API limit (attempt {attempt + 1}/{max_retries}). "
                      f"Retrying in {delay:.1f}s...")
                time.sleep(delay)
            else:
                raise  # Not a retriable error, or out of retries


def main():
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable is not set.")
        sys.exit(1)

    print("--- Starting Grammar & AI Pipeline ---")

    # Step 1: No API call — no retry needed
    print("\n[Step 1] Interpreting raw text into JSON...")
    try:
        interpret_questions(
            rules_src="rules.txt",
            questions_src="questions.txt",
            output_dest="interpretacion.txt"
        )
        print("✅ Saved parsed data to 'interpretacion.txt'")
    except Exception as e:
        print(f"❌ Interpretation failed: {e}")
        sys.exit(1)

    # Step 2: First OpenAI call — wrapped with retry
    print("\n[Step 2] Sending interpretation to OpenAI...")
    with_retry(ask_openai,
               input_file="interpretacion.txt",
               output_file="output_file.txt")
    print("✅ OpenAI response saved.")

    # Pause between calls to stay under rate limits
    time.sleep(1.5)

    # Step 3: Second OpenAI call — wrapped with retry
    print("\n[Step 3] Back-translating AI's response...")
    with_retry(back_translate,
               response_file="output_file.txt",
               rules_file="rules.txt",
               output_file="interpretationAI.txt")
    print("✅ Back-translation complete.")

    time.sleep(1.5)

    # Step 4: Third OpenAI call (TTS) — wrapped with retry
    print("\n[Step 4] Converting to audio...")
    audio_path = with_retry(text_to_audio,
                            input_file="interpretationAI.txt",
                            output_file="final_output_audio.wav")

    if audio_path:
        print(f"\n🎉 Pipeline finished! Listen to: {audio_path}")


if __name__ == "__main__":
    main()