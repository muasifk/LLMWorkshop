
import os
from google import genai
from google.genai import types
from google.genai.types import ModelContent, Part, UserContent
from dotenv import load_dotenv
from pathlib import Path


#=========================================================
# 1. Configuration
#=========================================================
# Load Gemini Key
load_dotenv(Path(__file__).resolve().parent.parent.parent / 'KEYS' / 'keys.env')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
#==========================================================




system_prompt = """
You are a task-structuring assistant. A user will give you a list of tasks. For each task:

1. Estimate the Time Requirement:
   - Short: <15 min
   - Medium: 15–60 min
   - Long: >60 min

2. Estimate the Cognitive Complexity:
   - Low, Medium, or High

3. Assess AI Involvement:
   - Can AI (like you) help with this task (Yes/No)? If so, say how.
   - Provide a suggested prompt the user could give to Gemini to get help.

Respond in a tabular format as follows:
| Task Description | Time Requirement | Cognitive Complexity | AI Involvement | AI Help Description | Starter Prompt |
|---|---|---|---|---|---|---|
| Task 1 | Short/Medium/Long | Low/Medium/High | Yes/No | Description of how AI can help | Suggested prompt for Gemini |

Only return the Table structure. No other text.
"""




# Gemini API client setup
client = genai.Client(api_key=GEMINI_API_KEY)
chat = client.chats.create(
    model='gemini-2.0-flash-exp',  # Updated to available model
    history=[
        UserContent(parts=[Part(text=system_prompt)]),
        ModelContent(parts=[Part(text="I understand. I'm ready to help structure tasks according to your requirements. Please provide me with a list of tasks to analyze.")]),
    ]
)

### The chat assistance starts here
print("Task Structuring Assistant - Powered by Gemini")
print("Provide a list of tasks, and I'll analyze them for you.")
print("Type 'exit' to quit\n")

try:
    while True:
        prompt = input("[User:] > ")
        if prompt.lower() == 'exit':
            break
        
        # Send the user's message
        response = chat.send_message(prompt)
        
        ### Save to markdown
        response_text = response.text.strip()
        with open("output.md", 'w', encoding='utf-8') as f:
            f.write(response_text)
            print('The tasks have been saved to output.md')

        # print("[Assistant:] > ", response.text)
        print()  # New line after response

except KeyboardInterrupt:
    print("\nExiting chat.")
except Exception as e:
    print(f"An error occurred: {e}")


'''
Example prompt:

I need to do several tasks tomorrow i.e., wash my car, buy groceries, attend parent-teacher meeting at the school, prepare a presentation for the team meeting next week, and submitting an urgent report before night.
'''