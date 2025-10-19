
# pip install google-genai
# pip install python-dotenv

from dotenv import load_dotenv
import os
# from google.generativeai import configure, list_models, GenerativeModel
from google import genai
from google.genai import types
from pathlib import Path
load_dotenv(Path(__file__).resolve().parent.parent.parent / 'KEYS' / 'keys.env')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
  


client = genai.Client(api_key=GEMINI_API_KEY)
model_name = 'gemini-2.0-flash-lite'  # Update if needed after checking available models
model = client.models.get(model_name)

chat = model.start_chat(history=[])

print("Stateful Chat [Client-based]. Type 'exit' to quit.")
while True:
    user_input = input("> ")
    if user_input.lower() == "exit":
        break

    response = chat.send_message(user_input)
    print(response.text)
















# chat_session = client.chats.create(
# model=model_name,
# config=types.GenerateContentConfig(
#     temperature=0.1,
#     top_p=0.95,
#     top_k=20,
#     candidate_count=1,
#     seed=5,
#     max_output_tokens=200,
#     stop_sequences=['STOP!'],
#     presence_penalty=0.0,
#     frequency_penalty=0.0,),
# history=[] # You can provide initial history here if needed, otherwise leave empty
# )



# print("Type your prompts (type 'exit' to quit):")
# try:
#     while True:
#         prompt = input("> ")
#         if prompt.lower() == 'exit':
#             break
#         response_stream = chat_session.send_message(prompt) # stream=True
#         for chunk in response_stream:
#             print(chunk.text, end='')
#         print() # Add a newline after the full response

# except KeyboardInterrupt:
#     print("\nExiting chat.")

