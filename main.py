import os
import sys
import time
import random
 
from parseador import interpret_questions
from openR import ask_ai, back_translate
from errorTTS import text_to_audio
 
 
def with_retry(fn, *args, max_retries=5, base_delay=2.0, **kwargs):
    for attempt in range(max_retries):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            err = str(e)
            is_retriable = any(code in err for code in ["429", "500", "502", "503"])
            if is_retriable and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                print(f"  ⚠️  API error (attempt {attempt + 1}/{max_retries}). Retrying in {delay:.1f}s...")
                time.sleep(delay)
            else:
                raise
 
 
def main():
    input_rules_path = "rules.json"
    input_questions_path = "questions1.txt"
    tmp_output_interpreter_path = "interpretacion.json"
    output_text_file = "output_file.txt"
    output_audio_file = "audio_answer.wav"

    if not os.environ.get("OPENROUTER_API_KEY"):
        print("ERROR: OPENROUTER_API_KEY environment variable is not set.")
        print("Please set it in your terminal before running: export OPENROUTER_API_KEY='sk-or-...'")
        sys.exit(1)
 
    print("--- Starting Grammar & AI Pipeline ---")
 
    print("\n[Step 1] Interpreting raw text into JSON...")
    try:
        interpret_questions(
            rules_src=input_rules_path,
            questions_src=input_questions_path,
            output_dest=tmp_output_interpreter_path
        )
        print(f"✅ Saved parsed data to '{tmp_output_interpreter_path}'")
    except Exception as e:
        print(f"❌ Interpretation failed: {e}")
        sys.exit(1)
 
    print("\n[Step 2] Sending interpretation to OpenRouter...")
    with_retry(ask_ai,
               input_file=tmp_output_interpreter_path,
               output_file=output_text_file)
 
    time.sleep(1.5)
 
    print("\n[Step 3] Back-translating AI's response to custom language...")
    with_retry(back_translate,
               response_file=output_text_file,
               rules_file=input_rules_path,
               output_file="interpretationAI.txt")
 
    time.sleep(1.5)
 
    print("\n[Step 4] Converting the custom language response to Audio (TTS)...")
    audio_path = with_retry(text_to_audio,
                            input_file="interpretationAI.txt",
                            output_file=output_audio_file)
 
    if audio_path:
        print(f"\n🎉 Pipeline Finished Successfully! You can listen to: {audio_path}")
 
 
if __name__ == "__main__":
    main()