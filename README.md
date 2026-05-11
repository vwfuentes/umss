# Grammar & AI Pipeline

A comprehensive Python project that processes natural language questions through a custom grammar parser, analyzes them with AI (via OpenRouter), and converts responses to audio using text-to-speech.

## Project Overview

This project implements a complete pipeline that:
1. **Parses** raw text into structured JSON using custom grammar rules
2. **Analyzes** parsed data using OpenRouter's GPT-4o-mini model
3. **Back-translates** AI responses into custom language format
4. **Converts** responses to audio (WAV format) using OpenRouter's TTS service

The pipeline includes built-in retry logic to handle API rate limits and transient errors.

## Prerequisites

- Python 3.8 or higher
- OpenRouter API key (get one at https://openrouter.ai)
- pip (Python package manager)

## Installation & Setup

### 1. Clone or Navigate to the Project

```bash
cd /path/to/umss
```

### 2. Create a Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate
```

**On Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Your OpenRouter API Key

**On Windows (PowerShell):**
```powershell
$env:OPENROUTER_API_KEY='your-api-key-here'
```

**On Windows (Command Prompt):**
```cmd
set OPENROUTER_API_KEY=your-api-key-here
```

**On macOS/Linux:**
```bash
export OPENROUTER_API_KEY='your-api-key-here'
```

To make this permanent, add it to your system environment variables or `.env` file.

## Usage

### Running the Pipeline

```bash
python main.py
```

### Input Files Required

The project expects the following files in the project directory:
- **rules.json** - Grammar rules for parsing questions
- **questions1.txt** - Raw questions to be processed

### Output Files Generated

- **interpretacion.json** - Parsed questions in JSON format
- **output_file.txt** - AI's raw response
- **interpretationAI.txt** - AI response in custom language format
- **audio_answer.wav** - Generated audio file

## Project Structure

```
umss/
├── main.py                    # Main pipeline orchestrator
├── parseador.py               # Grammar parser and JSON validator
├── openR.py                   # OpenRouter API interactions
├── errorTTS.py                # Text-to-speech audio generation
├── requirements.txt           # Python dependencies
├── rules.json                 # Grammar rules (input)
├── questions1.txt             # Questions to process (input)
├── interpretacion.json        # Parsed questions (output)
├── output_file.txt            # AI response (output)
├── interpretationAI.txt       # Back-translated response (output)
├── audio_answer.wav           # Generated audio (output)
└── textos/                    # Text samples and rules
```

## Configuration

### Environment Variables

- **OPENROUTER_API_KEY** (required) - Your OpenRouter API authentication key

### API Models Used

- **LLM Model:** `openai/gpt-4o-mini` - For question analysis
- **TTS Model:** `openai/gpt-4o-mini-tts-2025-12-15` - For text-to-speech

## Troubleshooting

### API Key Not Found Error
Make sure the `OPENROUTER_API_KEY` environment variable is set before running the script.

### Retry Logic
The pipeline automatically retries on API errors (429, 500, 502, 503) with exponential backoff. Maximum 5 attempts per operation.

### File Not Found Error
Ensure all required input files (`rules.json`, `questions1.txt`) exist in the project directory.

## Dependencies

- **jsonschema** - For validating grammar rules against JSON schema

All other dependencies are from Python's standard library:
- urllib - HTTP requests
- json - JSON parsing
- os - Environment variables
- time & random - Retry logic
- wave & struct - WAV audio generation

## License

This project is for educational and development purposes.
