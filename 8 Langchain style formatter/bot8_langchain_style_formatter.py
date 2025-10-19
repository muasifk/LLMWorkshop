
from dotenv import load_dotenv
import os
from datetime import datetime
from google import genai
from google.genai import types
from google.genai.types import GenerateContentConfig, Tool, FunctionDeclaration, Part
import requests
import json
import pandas as pd
# from call_gemini_api import call_gemini_api
from pathlib import Path

load_dotenv(Path(__file__).resolve().parent.parent.parent / 'KEYS' / 'keys.env')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

model  = 'gemini-2.0-flash-lite'
client = genai.Client(api_key=GEMINI_API_KEY)

