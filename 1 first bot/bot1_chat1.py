


# pip install google-genai
# pip install python-dotenv

from dotenv import load_dotenv
import os
from google import genai
from google.genai import types
load_dotenv(Path(__file__).resolve().parent.parent.parent / 'KEYS' / 'keys.env')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')




##############################################################
# The chat assistance using "generate_content_stream" method
##############################################################
client = genai.Client(api_key=GEMINI_API_KEY)
print("Type your prompts (type 'exit' to quit):")
try:
    while True:
        prompt = input("[User:] > ")
        if prompt.lower() == 'exit':
            break

        # Show response in streaming mode
        for chunk in client.models.generate_content_stream(
            model='gemini-2.0-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction='You are a helpful assistant who answers any questions in a concise way.',
                max_output_tokens= 1000,
                temperature= 0.6,  # range(0,1), higher value mean more creative/random
                safety_settings= [types.SafetySetting(
                        category='HARM_CATEGORY_HATE_SPEECH',
                        threshold='BLOCK_ONLY_HIGH'),]
                ),
            ):
            print(chunk.text)

        print()  # New line after response

except KeyboardInterrupt:
    print("\nExiting chat.")





