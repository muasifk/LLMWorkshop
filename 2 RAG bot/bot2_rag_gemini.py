

# conda activate llm-env
# conda create -n llm-env
# pip install google-genai
# pip install python-dotenv
# pip install PyMuPDF                  # pdf parser
# pip install faiss-cpu                # Meta's library for similarity search and clustering of dense vectors
# pip install sentence-transformers    # Python framework for sentence, text and image embeddings

#### PDF extraction libs:
# PyPDF2: text, limited image (no table)
# PyMuPDF: strong text, strong images, custom (not built in) table 
# PDFMiner: text, no image and table (complex to use)
# Tabula-py: tables, limited text (no image)
# Camelot: text, tables (cumbersome)




from dotenv import load_dotenv
import os
import numpy as np
from google import genai
from google.genai import types
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer
import faiss
from pathlib import Path
load_dotenv(Path(__file__).resolve().parent.parent.parent / 'KEYS' / 'keys.env')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
# from call_gemini import call_gemini
from rag_pipeline2 import load_documents
from rag_pipeline2 import chunk_text, smart_chunk
from rag_pipeline2 import embed_chunks, build_index, retrieve_chunks


DATA_DIR = "data"
EMBED_MODEL = SentenceTransformer('all-MiniLM-L6-v2') # 512 tokens
# EMBED_MODEL = SentenceTransformer('all-mpnet-base-v2')  # 514 tokens
# EMBED_MODEL = SentenceTransformer('sentence-transformers/all-MiniLM-L12-v2') # Longer context
# EMBED_MODEL = SentenceTransformer('BAAI/bge-large-en-v1.5') # SOTA
# EMBED_MODEL = SentenceTransformer('BAAI/bge-base-en-v1.5') # SOTA
# EMBED_MODEL = SentenceTransformer('allenai/scibert_scivocab_uncased') # technical/scientific
# EMBED_MODEL = SentenceTransformer('nlpaueb/legal-bert-base-uncased') # Legal
# EMBED_MODEL = SentenceTransformer('ProsusAI/finbert') # Financial




client = genai.Client(api_key=GEMINI_API_KEY)
def call_gemini(prompt, max_tokens=500, temperature=0.6):
    """Wrapper for Gemini API calls with error handling"""
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
            system_instruction="You are a helpful assistant. Use the following context to answer the user's question.",
            max_output_tokens= 300,
            # top_k= 2,
            # top_p= 0.5,
            temperature= 0.5, # 0: Deterministic response
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
    





def generate_response(query, retrieved_chunks, max_tokens=1000, temperature=0.6):
    context = "\n\n".join(retrieved_chunks)

    prompt = f"""
    Context:{context}
    Question: {query}
    If the answer is not in the context, say "I don't know."
    Answer:
    """
    return call_gemini(prompt, max_tokens, temperature)
    


### My RAG bot here
if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')

    # ---------- Preprocess Once ----------
    raw_text   = load_documents(DATA_DIR)
    chunks = chunk_text(raw_text, chunk_size=800, overlap=400)  # Character-based chunking
    # chunks     = smart_chunk(raw_text, max_size=500, overlap=50)  # Smart chunking
    embeddings = embed_chunks(chunks, EMBED_MODEL)
    index      = build_index(embeddings)
    


    print("RAG chatbot ready. Ask your questions (type 'exit' to quit):")
    while True:
        print()
        prompt = input("You > ")
        if prompt.lower() == "exit":
            break
        context_chunks = retrieve_chunks(prompt, chunks, index, EMBED_MODEL)
        answer = generate_response(prompt, context_chunks)
        print("\nAnswer:", answer)