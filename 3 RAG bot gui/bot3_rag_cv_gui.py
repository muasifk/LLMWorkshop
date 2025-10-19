

# conda activate llm-env
# conda create -n llm-env
# pip install google-generativeai
# pip install gradio

#### PDF extraction libs:
# PyPDF2: text, limited image (no table)
# PyMuPDF: strong text, strong images, custom (not built in) table 
# PDFMiner: text, no image and table (complex to use)
# Tabula-py: tables, limited text (no image)
# Camelot: text, tables (cumbersome)
# pip install PyMuPDF # pdf parser
# pip install faiss-cpu  # Meta's library for similarity search and clustering of dense vectors
# pip install sentence-transformers # Python framework for sentence, text and image embeddings


import numpy as np
import os
import google.generativeai as genai
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer
import faiss
import gradio as gr
from dotenv import load_dotenv
from pathlib import Path

DATA_DIR = "data"
EMBED_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
# api_key = os.getenv('GOOGLE_API_KEY')
# load_dotenv('../keys.env')  # Load environment variables from .env file
load_dotenv(Path(__file__).resolve().parent.parent.parent / 'KEYS' / 'keys.env')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)
gemini = genai.GenerativeModel('gemini-2.0-flash-lite')




# ---------- PDF Processing ----------
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def load_documents(data_dir):
    return "\n".join(
        extract_text_from_pdf(os.path.join(data_dir, f))
        for f in os.listdir(data_dir)
        if f.endswith(".pdf")
    )

def chunk_text(text, chunk_size=500, overlap=50):
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunks.append(text[i:i+chunk_size])
    return chunks

def embed_chunks(chunks):
    return np.array(EMBED_MODEL.encode(chunks))

def build_index(embeddings):
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    return index

def retrieve_chunks(query, chunks, index, top_k=3):
    query_vec = EMBED_MODEL.encode([query])
    distances, indices = index.search(np.array(query_vec), top_k)
    return [chunks[i] for i in indices[0]]


def generate_response(query, retrieved_chunks):
    context = "\n\n".join(retrieved_chunks)
    prompt = f"""You are an assistant that answers questions based on the user's documents.

Context:
{context}

Question: {query}
Answer:"""
    response = gemini.generate_content(prompt)
    return response.text


# ---------- Preprocess Once ----------
raw_text   = load_documents(DATA_DIR)
chunks     = chunk_text(raw_text)
embeddings = embed_chunks(chunks)
index      = build_index(embeddings)



# ---------- Gradio UI ----------
def chat_interface(user_input, history):
    context_chunks = retrieve_chunks(user_input, chunks, index)
    answer = generate_response(user_input, context_chunks)
    history.append((user_input, answer))
    return answer, history

gr.ChatInterface(fn=chat_interface).launch()
# gr.ChatInterface(fn=chat_interface, title="About M. A. Khan", description="Ask questions about your CV and research statement.").launch()
