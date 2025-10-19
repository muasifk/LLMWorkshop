
import os
import numpy as np
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer
import faiss
from pathlib import Path





def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    # print(f"Reading {len(doc)} pages from {pdf_path}")
    text = ""
    for page in doc:
        text += page.get_text()
    return text



def load_documents(data_dir):
    return "\n".join(
        extract_text_from_pdf(os.path.join(data_dir, f))
        for f in os.listdir(data_dir)
        if f.endswith(".pdf"))


def chunk_text(text, chunk_size=500, overlap=50):
    '''
    Character-based Text Chunking
    '''
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunks.append(text[i:i+chunk_size])
    # print('\n A sample chunk \n', chunks[0],'\n')
    return chunks



def embed_chunks(chunks):
    embeddings = EMBED_MODEL.encode(chunks)
    # print('Show embeddings \n', embeddings[0], '\n')
    return np.array(embeddings)



def build_index(embeddings):
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    # print('Show Index \n', index, '\n')
    return index



def retrieve_chunks(query, chunks, index, embedding_model, top_k=3):
    '''
    Retrieve Relevant Chunks for a Query
    '''
    query_vec = embedding_model.encode([query])
    distances, indices = index.search(np.array(query_vec), top_k)
    return [chunks[i] for i in indices[0]]


