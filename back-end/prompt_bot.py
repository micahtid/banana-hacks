import os
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables from .env file
load_dotenv()

def extract_code(text: str) -> str:
    """Extract the code from the text"""
    match = re.search(r"```python(.*)```", text, re.DOTALL)
    return match.group(1).strip() if match else ""

def create_bot_prompt() -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    client = genai.Client(api_key=api_key)
    prompt = """Write a hello world program in Python. 
Output ONLY the executable Python code with no explanations, no markdown formatting, no code fences, and no comments.
Just the raw Python code that can be directly executed."""
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=500,
            )
        )
        code = response.text.strip()
        exec(code)
        return code
    except Exception as e:
        print(f"Error generating code: {e}")
        return ""

code = create_bot_prompt()
print(code)
