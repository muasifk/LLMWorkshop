
import os, time, random
from google import genai
from google.genai import types
from google.genai.types import ModelContent, Part, UserContent
from dotenv import load_dotenv
from pathlib import Path
import json



#=========================================================
# 1. Configuration
#=========================================================
# Load Gemini Key
load_dotenv(Path(__file__).resolve().parent.parent.parent / 'KEYS' / 'keys.env')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
client = genai.Client(api_key=GEMINI_API_KEY)


#==========================================================

topics = [
    "geography", "science", "technology", "mathematics", "literature",
    "space", "biology", "history", "computer programming", "physics",
    "chemistry", "sports", "culture", "logic", "daily knowledge"
]



dataset = []
samples_per_topic = 50  # 15 * 350 ≈ 5250





for topic in topics:
    for i in range(samples_per_topic // 10):  # each batch: 10 QA pairs
        prompt = (
            f"Generate 10 diverse general knowledge question-answer pairs about {topic}.\n"
            f"Output strictly in JSON Lines format where each line is like:\n"
            f'{{"input": "question text", "output": "answer text"}}\n'
            f"Questions should be factual and concise."
        )

        try:
            # response = model.generate_content(prompt)
            response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.8,
                        ),
                    )
            text = response.text.strip()

            for line in text.split("\n"):
                try:
                    obj = json.loads(line)
                    dataset.append(obj)
                except:
                    continue

            print(f"{topic}: {len(dataset)} samples so far.")
            # time.sleep(random.uniform(0.8, 1.5))  # avoid rate limits
            time.sleep(random.uniform(2, 4))  # avoid rate limits

        except Exception as e:
            print(f"Error with {topic}: {e}")
            time.sleep(3)

# --- Save to file ---
with open("data_general_qa.jsonl", "w", encoding="utf-8") as f:
    for item in dataset:
        json.dump(item, f, ensure_ascii=False)
        f.write("\n")

print(f"✅ Saved {len(dataset)} QA pairs to general_qa_5000_gemini.jsonl")