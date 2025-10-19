
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from pathlib import Path

# Load Gemini Key
load_dotenv(Path(__file__).resolve().parent.parent.parent / 'KEYS' / 'keys.env')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')




def call_gemini(prompt, max_tokens=500, temperature=0.6):
    client = genai.Client(api_key=GEMINI_API_KEY)
    """Wrapper for Gemini API calls with error handling"""
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
            # system_instruction='you are a story teller for kids under 5 years old',
            max_output_tokens= 300,
            # top_k= 2,
            # top_p= 0.5,
            temperature= 0.5,
            #   response_mime_type= 'application/json',
            stop_sequences= ['\n'],
            seed=42,
            safety_settings= [types.SafetySetting(
                    category='HARM_CATEGORY_HATE_SPEECH',
                    threshold='BLOCK_ONLY_HIGH'),]
            ),)
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