# pip install langchain, chromadb, pypdf
import os
from google import genai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
from sentence_transformers import SentenceTransformer
import chromadb
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).resolve().parent.parent.parent / 'KEYS' / 'keys.env')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
client = genai.Client(api_key=GEMINI_API_KEY)



class AcademicStyleTransformer:
    def __init__(self):
        # Initialize components
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        self.gemini_client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
        
        # Setup vector database
        self.client = chromadb.PersistentClient(path="./style_db")
        self.collection = self.client.get_or_create_collection(
            name="academic_style",
            metadata={"hnsw:space": "cosine"}
        )
        
        self.style_examples = []
        self.is_trained = False



    def train_on_papers(self, data_folder="data"):
        """Train the transformer on research papers from a folder"""
        print(f"Training on research papers from '{data_folder}' folder...")
        
        # Get all PDF files from the data folder
        import glob
        pdf_files = glob.glob(os.path.join(data_folder, "*.pdf"))
        if not pdf_files:
            print(f"No PDF files found in '{data_folder}' folder!")
            return
        print(f"Found {len(pdf_files)} PDF files")
        
        all_chunks = []
        all_texts = []
        for pdf_path in pdf_files:
            print(f"Processing: {os.path.basename(pdf_path)}")
            try:
                # Load PDF
                loader = PyPDFLoader(pdf_path)
                documents = loader.load() 
                # Extract text
                full_text = " ".join([doc.page_content for doc in documents])
                all_texts.append(full_text)
                # Split into chunks for style reference
                chunks = self.text_splitter.split_text(full_text)
                all_chunks.extend(chunks)
            except Exception as e:
                print(f"Error processing {pdf_path}: {e}")
                continue
        # Store chunks in vector database for style matching
        embeddings = [self.embedding_model.encode(chunk) for chunk in all_chunks]
        self.collection.add(
            documents=all_chunks,
            embeddings=embeddings,
            ids=[f"style_chunk_{i}" for i in range(len(all_chunks))]
        )
        
        # Keep best style examples
        self.style_examples = all_texts[:5]  # Top 5 papers as style references
        self.is_trained = True
        print(f"Training complete! Learned style from {len(pdf_files)} papers")



    def find_similar_style_examples(self, input_text, n_examples=2):
        """Find style examples similar to input text topic"""
        if not self.is_trained:
            return []
        input_embedding = self.embedding_model.encode(input_text)
        results = self.collection.query(
            query_embeddings=[input_embedding.tolist()],
            n_results=n_examples
        )
        return results['documents'][0] if results['documents'] else []
    


    def transform_text(self, input_text):
        """Transform input text to academic style"""
        if not self.is_trained:
            return "Error: Please train the transformer on research papers first."
        # Find similar style examples
        similar_examples = self.find_similar_style_examples(input_text)
        # Use general style examples if no similar ones found
        style_reference = similar_examples[0] if similar_examples else self.style_examples[0]
        # Create transformation prompt
        prompt = f"""Transform the following text to match the academic writing style of research papers.

        STYLE REFERENCE (match this writing style):
        {style_reference[:800]}

        INPUT TEXT TO TRANSFORM:
        {input_text}

        TRANSFORMATION GUIDELINES:
        1. Use formal academic tone and vocabulary
        2. Replace casual language with scholarly expressions
        3. Add hedging language ("may suggest", "appears to", "potentially indicates")
        4. Use more complex sentence structures
        5. Include precise, technical terminology where appropriate
        6. Maintain the original meaning and content
        7. Structure arguments more formally
        8. Use passive voice where suitable for academic writing

        TRANSFORMED TEXT:
        """
        response = self.gemini_client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=prompt
            )
        return response.text
    


    def batch_transform(self, text_list):
        """Transform multiple texts at once"""
        transformed_texts = []
        for i, text in enumerate(text_list):
            print(f"Transforming text {i+1}/{len(text_list)}...")
            transformed = self.transform_text(text)
            transformed_texts.append(transformed) 
        return transformed_texts








# Usage Examples
def main():
    # Initialize transformer
    transformer = AcademicStyleTransformer()
    
    # Train on research papers from 'data' folder
    transformer.train_on_papers("data")  # Will read all PDFs from data/ folder
    
    # Transform text examples
    casual_text = """
    The market size of civilian drones is tremendously increasing and is expected 
    to reach 1.66 million by the end of 2023. The increase in number of civilian 
    drones poses several privacy and security threats. 
    To safeguard critical assets and infrastructure and to protect privacy of people
      from the illegitimate uses of commercial drones, a drone detection system is 
      inevitable. In particular, there is a need for a drone detection system that 
      is efficient, accurate, robust, cost-effective and scalable. Recognizing the 
      importance of the problem, several drone detection approaches have been 
      proposed over time. However, none of these provides sufficient performance 
      due to the inherited limitations of the underlying detection technology. 
      More specifically, there are trade-offs among various performance metrics 
      e.g., accuracy, detection range, and robustness against environmental 
      conditions etc. This motivates an in-depth study and critical analysis of 
      the existing approaches, highlighting their potential benefits and limitations. 
      In this paper, we provide a rigorous overview of the existing drone detection 
      techniques and a critical review of the state-of-the-art. Based on the review, 
      we provide key insights on the future drone detection systems. We believe these 
      insights will provide researchers and practicing engineers a holistic view to 
      understand the broader context of the drone detection problem.
    """
    
    academic_text = transformer.transform_text(casual_text)
    
    print("ORIGINAL:")
    print(casual_text)
    print("\nTRANSFORMED:")
    print(academic_text)
    
    # Interactive mode
    print("\n" + "="*50)
    print("Interactive Style Transformer")
    print("Type 'quit' to exit")
    print("="*50)
    
    while True:
        user_input = input("\nEnter text to transform: ")
        
        if user_input.lower() in ['quit', 'exit']:
            break
            
        if not user_input.strip():
            continue
            
        try:
            transformed = transformer.transform_text(user_input)
            print(f"\nTransformed: {transformed}")
        except Exception as e:
            print(f"Error: {e}")




##### Or without main
# transformer = AcademicStyleTransformer()
# transformer.train_on_papers("data")
# result = transformer.transform_text("Your text here")
# print(result)


# Simple API-like usage (Simplified wrapper)
# class StyleTransformerAPI:
#     def __init__(self, data_folder="data"):
#         self.transformer = AcademicStyleTransformer()
#         self.transformer.train_on_papers(data_folder)
    
#     def transform(self, text):
#         """Simple transform method"""
#         return self.transformer.transform_text(text)
    
#     def transform_multiple(self, texts):
#         """Transform list of texts"""
#         return self.transformer.batch_transform(texts)



# Example usage of the API
# def api_example():
#     # Initialize with papers from data folder
#     api = StyleTransformerAPI("data")
    
#     # Transform single text
#     result = api.transform("This method works really well for our problem.")
#     print(result)
    
#     # Transform multiple texts
#     texts = [
#         "The results look good.",
#         "We found some interesting patterns.",
#         "This approach might be useful."
#     ]
    
#     results = api.transform_multiple(texts)
#     for original, transformed in zip(texts, results):
#         print(f"Original: {original}")
#         print(f"Transformed: {transformed}\n")



if __name__ == "__main__":
    main()