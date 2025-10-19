

from dotenv import load_dotenv
import os
from datetime import datetime
from google import genai
from google.genai import types
from google.genai.types import GenerateContentConfig, Tool, FunctionDeclaration, Part
import requests
import json
import pandas as pd
from pathlib import Path

# from call_gemini_api import call_gemini_api
from get_weather_forecast import get_weather_forecast, get_weather_forecast_func, call_function

load_dotenv(Path(__file__).resolve().parent.parent.parent / 'KEYS' / 'keys.env')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

model  = 'gemini-2.0-flash-lite'
client = genai.Client(api_key=api_key)
# chat  = client.chats.create(model=model)



# Global conversation history
history = []
#===========================================================================================
def tourism_agent(prompt):
    global history
    #####  Step 1: Take the prompt and generate the initial response
    today = datetime.now().strftime("%Y-%m-%d")

    # Initialize conversation if empty
    if not history:
        history = []

    config = GenerateContentConfig(
    # system_instruction="You are a helpful assistant that use tools to access and retrieve information from a weather API. Today is 2025-06-15.", # to give the LLM context on the current date.
    # system_instruction=f"You are a helpful assistant that can answer various questions and help with different tasks. You have access to weather information through a weather API when needed. Today is {today}. Use the weather tool when users ask about weather conditions.",
    system_instruction=f"You are a helpful tourism assistant that can help with various travel-related questions. You have access to weather information through a weather API when needed. Today is {today}. You can discuss destinations, attractions, travel tips, and provide weather forecasts when requested.",
    tools=[{"function_declarations": [get_weather_forecast_func]}], # define the functions that the LLM can use
    )

    # history = [types.Content(role="user", parts=[types.Part(text=prompt)])]
    history.append(types.Content(role="user", parts=[types.Part(text=prompt)])) # For history
    
    # initial response 
    response = client.models.generate_content(
        model=model,
        config=config,
        contents=history,
    )

    ##### Step 2: Function call
    for part in response.candidates[0].content.parts:
        # add response to the conversation
        history.append(types.Content(role="model", parts=[part]))

        # check if the response is a function call
        if part.function_call:
            print("Tool call detected")
            function_call = part.function_call

            # Call the tool with arguments
            # print(f"Calling tool: {function_call.name} with args: {function_call.args}")
            tool_result = call_function(function_call.name, **function_call.args)
            
            # Build the response parts using the function result.
            function_response_part = types.Part.from_function_response(
                name=function_call.name,
                response={"result": tool_result},
            )
            history.append(types.Content(role="user", parts=[function_response_part]))


            # Send follow-up with tool results, but remove the tools from the config
            # print(f"Calling LLM with tool results")
            func_gen_response = client.models.generate_content(
                model=model, config=config, contents=history
            )
            # Add the response to the conversation
            history.append(types.Content(role="model", parts=func_gen_response.candidates[0].content.parts))
    # return the final response
    return history[-1].parts[0].text.strip()


def reset_conversation():
    """Reset the conversation history"""
    global history
    history = []
    print("Conversation reset.")
#===========================================================================================

### Run Agent
print("Type your prompts (type 'exit' to quit):")
try:
    while True:
        prompt = input("[You] > ")
        if prompt.lower() == 'exit':
            break
        elif prompt.lower() == 'reset':
            reset_conversation()
            continue

        response_agent = tourism_agent(prompt)
        print("[Tourism Agent] > ", response_agent)  
        print()     # New line after response

except KeyboardInterrupt:
    print("\nExiting chat.")





