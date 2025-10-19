
## 1 Install Librraies (if not already installed)
# pip install google-genai
# pip install python-dotenv

## 2 Import libraries
from dotenv import load_dotenv
import os
from google import genai
from google.genai import types
from pathlib import Path

load_dotenv(Path(__file__).resolve().parent.parent.parent / 'KEYS' / 'keys.env')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
  
## 4 Initialize a client instance.
client = genai.Client(api_key=api_key)

## 4 Create the response using the "generate_content()" method 
##   from the models interface of the client object.
response = client.models.generate_content(
    model='gemini-2.0-flash',  # the chosen gemini model
    contents='Tell me a story about titans in at least 200 words.', # This is the user prompt
    config=types.GenerateContentConfig(
      system_instruction='You are a story teller with a good common sense who can generate nice stories for kids',
      max_output_tokens= 5000,
      temperature= 0.6,  # range(0,1), higher value mean more creative/random
      # seed=42,           # reproducibility
      safety_settings= [types.SafetySetting(
              category='HARM_CATEGORY_HATE_SPEECH',
              threshold='BLOCK_ONLY_HIGH'),]
    ),
)

# os.system('cls' if os.name == 'nt' else 'clear')
print(response.text)



























# print(response.model_dump_json(exclude_none=True, indent=4))





## 4 Create
# response = client.models.generate_content(
#     model='gemini-2.0-flash',
#     contents='Tell me a story of a titans in at least 50 lines.',
#     config=types.GenerateContentConfig(
#       system_instruction='You are a story teller with a good common sense',
#       max_output_tokens= 5000,
#       # top_k= 2,
#       # top_p= 0.5,
#       temperature= 0.6,
#     #   response_mime_type= 'application/json',
#       stop_sequences= ['\n'],
#       seed=42,
#       safety_settings= [types.SafetySetting(
#               category='HARM_CATEGORY_HATE_SPEECH',
#               threshold='BLOCK_ONLY_HIGH'),]
#     ),
# )

# os.system('cls' if os.name == 'nt' else 'clear')
# print(response.text)