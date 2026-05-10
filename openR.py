import urllib.request
import json
import os
 
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
 
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            answer = result['choices'][0]['message']['content']
 
            with open(output_file, 'w', encoding='utf-8') as out:
                out.write(answer.strip())
 
            print(f"AI answer saved to {output_file}")
 
    except Exception as e:
        print(f"Failed to get AI response: {e}")
        raise  # lets with_retry in main see the error and retry
 
 
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
 
    prompt = (
        #f"I want to translate this ai_text.txt{ai_text} with this rules.txt{grammar_rules} to interpretationAI.txt(all the files are in the same directory)"
        f"Accord to this english text {ai_text}, if this english has 'Sorry, could you provide more info?, answer:'Sorry, could you provide more info?' if not translate it with grammar rules'.\n"
        f"Here are the grammar rules for a custom language, analize it:\n{grammar_rules}\n\n"
        f"Return ONLY the translated text, with no additional explanations.\n"
    )
 
    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }
 
    data = json.dumps(payload).encode('utf-8')
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {key}'
    }
 
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
 
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            translated_answer = result['choices'][0]['message']['content']
 
            with open(output_file, 'w', encoding='utf-8') as out:
                out.write(translated_answer.strip())
 
            print(f"AI translation saved to {output_file}")
 
    except Exception as e:
        print(f"Failed to translate using AI: {e}")
        raise  # lets with_retry in main see the error and retry
 