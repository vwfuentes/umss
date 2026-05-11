import urllib.request
import json
import os
import time
import random


# ── moved in from main.py ──────────────────────────────────────────────────

def _with_retry(fn, *args, max_retries=5, base_delay=2.0, **kwargs):
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


# ──────────────────────────────────────────────────────────────────────────

def ask_ai(input_file: str, output_file: str, api_key: str = None):
    """
    Reads text, sends a POST to OpenRouter, and saves the result.
    """
    key = api_key or os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise ValueError("API Key not found. Please set OPENROUTER_API_KEY.")

    with open(input_file, 'r', encoding='utf-8') as f:
        prompt_content = f.read()

    url = "https://openrouter.ai/api/v1/chat/completions"

    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Analyze this data, answer and provide a response summarized, answer the question, very short, if you don't have suffest information say, sorry, could you provide more info?: {prompt_content}"}
        ]
    }

    data = json.dumps(payload).encode('utf-8')
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {key}'
    }

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    def _do_request():
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            answer = result['choices'][0]['message']['content']

            with open(output_file, 'w', encoding='utf-8') as out:
                out.write(answer.strip())

            print(f"AI answer saved to {output_file}")

    try:
        _with_retry(_do_request)
    except Exception as e:
        print(f"Failed to get AI response: {e}")
        raise


def back_translate(response_file: str, rules_file: str, output_file: str, api_key: str = None):
    """
    Translates response back to custom language using OpenRouter.
    """
    key = api_key or os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise ValueError("API Key not found. Please set OPENROUTER_API_KEY.")

    with open(response_file, 'r', encoding='utf-8') as f:
        ai_text = f.read().strip()

    with open(rules_file, 'r', encoding='utf-8') as f:
        grammar_rules = f.read().strip()

    url = "https://openrouter.ai/api/v1/chat/completions"

    # STRICT PROMPTING:
    system_prompt = (
        "You are an expert translator for a custom language. Your job is to translate English "
        "text into this custom language using the provided grammar rules. "
        "Return ONLY the translated text, with absolutely no additional text, quotation marks, or explanations."
    )

    user_prompt = (
        f"English text to translate: '{ai_text}'\n\n"
        f"Instructions:\n"
        "1. Use the grammar rules provided below to translate the English text.\n"
        "2. CRITICAL: If the English text says 'Sorry, could you provide more info?', "
        "you MUST ONLY use the 'UNKNOWN_INFO' DO NOT add anything more just the content of 'UNKNOWN_INFO'"
        "if YOU DON'T HAVE ANY INFORMATION DO NOT answer only with UNKNOWN_INFO'\n"
        f"Grammar Rules:\n{grammar_rules}"
    )

    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }

    data = json.dumps(payload).encode('utf-8')
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {key}'
    }

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    def _do_request():
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            translated_answer = result['choices'][0]['message']['content']

            with open(output_file, 'w', encoding='utf-8') as out:
                out.write(translated_answer.strip())

            print(f"AI translation saved to {output_file}")

    try:
        _with_retry(_do_request)
    except Exception as e:
        print(f"Failed to translate using AI: {e}")
        raise