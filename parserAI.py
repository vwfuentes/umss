import urllib.request
import json
import os
import re
import jsonschema

RULES_SCHEMA = {
    "type": "object",
    "properties": {
        "language_name": {"type": "string"},
        "rules": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "pattern": {"type": "string"},
                    "intent": {"type": "string"}
                },
                "required": ["id", "pattern", "intent"]
            }
        }
    },
    "required": ["language_name", "rules"]
}

def ask_gemini(input_file: str, output_file: str, api_key: str = None):
    """
    Simplified handler: Reads text, sends a POST to Gemini, and saves the result.
    """
    # 1. Get the Key
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("API Key not found.")

    # 2. Read the input text
    with open(input_file, 'r', encoding='utf-8') as f:
        prompt_content = f.read()

    # 3. Prepare URL and Payload
    # Using the standard stable flash model
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
    
    payload = {
        "contents": [{
            "parts": [{"text": f"Analyze this data and provide a response: {prompt_content}"}]
        }]
    }
    
    data = json.dumps(payload).encode('utf-8')
    headers = {'Content-Type': 'application/json'}
    
    # 4. Explicit POST Request
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            # Extract the text answer
            answer = result['candidates'][0]['content']['parts'][0]['text']
            
            # 5. Save the result
            with open(output_file, 'w', encoding='utf-8') as out:
                out.write(answer.strip())
                
            print(f"AI answer saved to {output_file}")

    except Exception as e:
        print(f"Failed to get AI response: {e}")

def interpret_ai_response(response_file: str, rules_file: str, output_file: str):
    """
    Deterministically parses the AI's short response using the JSON Schema and grammar rules,
    without making any external AI API calls.
    """
    # Read the AI's text
    with open(response_file, 'r', encoding='utf-8') as f:
        ai_text = f.read().strip()

    # Read the custom grammar rules
    with open(rules_file, 'r', encoding='utf-8') as f:
        rules_content = f.read().strip()

    # Convert text format to JSON if necessary
    if rules_content.startswith("{"):
        rules_data = json.loads(rules_content)
    else:
        rules_data = {"language_name": "ParsedText", "rules": []}
        for line in rules_content.splitlines():
            line = line.strip()
            if line.startswith("Name:"):
                rules_data["language_name"] = line.split(":", 1)[1].strip()
            elif line.startswith("Rule:"):
                parts = line.split("|")
                if len(parts) == 3:
                    r_id = parts[0].replace("Rule:", "").strip()
                    r_pat = parts[1].strip()
                    r_int = parts[2].strip()
                    rules_data["rules"].append({"id": r_id, "pattern": r_pat, "intent": r_int})

    # Validate against JSON Schema
    jsonschema.validate(instance=rules_data, schema=RULES_SCHEMA)

    # Interpret the AI text against the rules
    interpretations = []
    for line in ai_text.splitlines():
        line = line.strip()
        if not line:
            continue
        
        matched = False
        for rule in rules_data["rules"]:
            pattern = re.compile(rule["pattern"])
            match = pattern.match(line)
            if match:
                interpretations.append({
                    "ai_response_text": line,
                    "rule_id": rule["id"],
                    "intent": rule["intent"],
                    "extracted_groups": list(match.groups())
                })
                matched = True
                break
        
        if not matched:
            interpretations.append({
                "ai_response_text": line,
                "error": "No matching grammar rule found."
            })

    # Save the interpretation as JSON
    with open(output_file, 'w', encoding='utf-8') as out:
        json.dump(interpretations, out, indent=4)
    
    print(f"Local interpretation saved to {output_file}")
