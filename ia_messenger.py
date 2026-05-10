import urllib.request
import json
import os

def ask_openai(input_file: str, output_file: str, api_key: str = None):
    """
    Reads text, sends a POST to OpenAI, and saves the result.
    """
    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise ValueError("API Key not found. Please set OPENAI_API_KEY.")

    with open(input_file, 'r', encoding='utf-8') as f:
        prompt_content = f.read()

    # 1. New URL for OpenAI Chat Completions
    url = "https://api.openai.com/v1/chat/completions"
    
    # 2. New Payload format (OpenAI uses 'messages' and 'role')
    payload = {
        "model": "gpt-4o-mini", # Fast, cost-effective text model
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Analyze this data and provide a response summarized, very short: {prompt_content}"}
        ]
    }
    
    # 3. New Header format (Bearer token instead of URL parameter)
    data = json.dumps(payload).encode('utf-8')
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {key}'
    }
    
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            # 4. New Response Parsing logic
            answer = result['choices'][0]['message']['content']
            
            with open(output_file, 'w', encoding='utf-8') as out:
                out.write(answer.strip())
                
            print(f"AI answer saved to {output_file}")

    except Exception as e:
        print(f"Failed to get AI response: {e}")

def back_translate(response_file: str, rules_file: str, output_file: str, api_key: str = None):
    """
    Translates response back to custom language using OpenAI.
    """
    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise ValueError("API Key not found.")

    with open(response_file, 'r', encoding='utf-8') as f:
        ai_text = f.read().strip()

    with open(rules_file, 'r', encoding='utf-8') as f:
        grammar_rules = f.read().strip()

    url = "https://api.openai.com/v1/chat/completions"
    
    prompt = (
        f"Here are the grammar rules for a custom language:\n{grammar_rules}\n\n"
        f"Translate the following English text into this custom language, following the rules exactly.\n"
        f"Return ONLY the translated text, with no additional explanations.\n"
        f"Text to translate: {ai_text}"
    )
    
    payload = {
        "model": "gpt-4o-mini",
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

