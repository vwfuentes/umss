import os
import sys
import time
from parseador import interpret_questions
from ia_messenger import ask_openai, back_translate
from text_to_audio import text_to_audio

def main():
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable is not set.")
        sys.exit(1)

    print("--- Starting Grammar & AI Pipeline ---")

    # Step 1
    try:
        interpret_questions(
            rules_src="rules.txt",
            questions_src="questions.txt",
            output_dest="interpretacion.txt"
        )
        print("✅ Step 1: Interpretation saved.")
    except Exception as e:
        print(f"❌ Step 1 failed: {e}")
        sys.exit(1)

    # Step 2
    try:
        ask_openai(input_file="interpretacion.txt", output_file="output_file.txt")
        print("✅ Step 2: OpenAI answer saved.")
        # Verify the output file was created
        if not os.path.exists("output_file.txt") or os.path.getsize("output_file.txt") == 0:
            raise RuntimeError("Output file is missing or empty after API call.")
    except Exception as e:
        print(f"❌ Step 2 failed: {e}")
        sys.exit(1)

    # Step 3
    try:
        back_translate(
            response_file="output_file.txt",
            rules_file="rules.txt",
            output_file="interpretationAI.txt"
        )
        print("✅ Step 3: Back‑translation complete.")
        if not os.path.exists("interpretationAI.txt") or os.path.getsize("interpretationAI.txt") == 0:
            raise RuntimeError("Back‑translation output file is missing or empty.")
    except Exception as e:
        print(f"❌ Step 3 failed: {e}")
        sys.exit(1)

    # Step 4
    try:
        audio_path = text_to_audio(
            input_file="interpretationAI.txt",
            output_file="final_output_audio.wav"
        )
        print(f"\n🎉 Pipeline finished! Audio saved to: {audio_path}")
    except Exception as e:
        print(f"❌ Step 4 failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
