import os
import sys
import time

from parseador import interpret_questions
from ask_AI import ask_ai, back_translate
from tts import text_to_audio
from stt import stt


def main():
    input_rules_path            = "rules.json"
    tmp_stt_output_path         = "question_heard.txt"
    tmp_output_interpreter_path = "interpretacion.json"
    output_text_file            = "output_file.txt"
    output_audio_file           = "audio_answer.wav"

    if not os.environ.get("OPENROUTER_API_KEY"):
        print("ERROR: OPENROUTER_API_KEY is not set.")
        print("  Windows : $env:OPENROUTER_API_KEY='sk-or-...'")
        print("  Linux   : export OPENROUTER_API_KEY='sk-or-...'")
        sys.exit(1)

    print("--- Starting Grammar & AI Pipeline (Voice Input) ---")

    print("\n[Step 1] Listening to microphone...")
    question = stt()
    print(f"✅ Heard: '{question}'")

    # Save the transcribed text to a file so parseador can read it
    # exactly the same way it would read questions.txt
    with open(tmp_stt_output_path, "w", encoding="utf-8") as f:
        f.write(question)

    print("\n[Step 2] Interpreting heard text using grammar rules...")
    try:
        interpret_questions(
            rules_src=input_rules_path,
            questions_src=tmp_stt_output_path,
            output_dest=tmp_output_interpreter_path
        )
        print(f"✅ Saved parsed data to '{tmp_output_interpreter_path}'")
    except Exception as e:
        print(f"❌ Interpretation failed: {e}")
        sys.exit(1)

    print("\n[Step 3] Sending interpretation to OpenRouter...")
    ask_ai(
        input_file=tmp_output_interpreter_path,
        output_file=output_text_file
    )

    time.sleep(1.5)

    print("\n[Step 4] Back-translating AI's response to custom language...")
    back_translate(
        response_file=output_text_file,
        rules_file=input_rules_path,
        output_file="interpretationAI.txt"
    )

    time.sleep(1.5)

    print("\n[Step 5] Converting the custom language response to Audio (TTS)...")
    audio_path = text_to_audio(
        input_file="interpretationAI.txt",
        output_file=output_audio_file
    )

    if audio_path:
        print(f"\n🎉 Pipeline Finished Successfully! You can listen to: {audio_path}")


if __name__ == "__main__":
    main()