
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from pathlib import Path

# Load Gemini Key
load_dotenv(Path(__file__).resolve().parent.parent.parent / 'KEYS' / 'keys.env')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

client = genai.Client(api_key=GEMINI_API_KEY)

def call_gemini(prompt, max_tokens=1000, temperature=0.6):
    """Wrapper for Gemini API calls with error handling"""
    try:
        
        response = client.models.generate_content(
            model='gemini-2.0-flash-lite',
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=max_tokens, 
                temperature=temperature
            )
        )
        return response.text.strip()
    except Exception as e:
        print(f"Gemini API error: {str(e)}")
        return None
    


print("RAG chatbot ready. Ask your questions (type 'exit' to quit):")
while True:
    print()
    prompt = input("You > ")
    if prompt.lower() == "exit":
        break
    answer = call_gemini(prompt)
    print("\nAnswer:", answer)