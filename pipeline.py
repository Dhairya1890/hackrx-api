import os
from dotenv import load_dotenv
from tqdm import tqdm
from langchain.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.base import Embeddings
import google.generativeai as genai
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from google.generativeai import GenerativeModel

# ===============================
# 1. Load Environment Variables
# ===============================
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ===============================
# 2. Gemini Embedding Wrapper
# ===============================
class GeminiEmbeddings(Embeddings):
    def embed_query(self, text: str):
        return genai.embed_content(model="embedding-001", content=text)["embedding"]
    def embed_documents(self, texts):
        return [self.embed_query(t) for t in texts]

embedding_model = GeminiEmbeddings()

# ===============================
# 3. Load & Split PDFs
# ===============================
def load_and_chunk(directory="documents/"):
    loader = PyPDFDirectoryLoader(directory)
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    return splitter.split_documents(docs)

print("📂 Loading documents...")
documents = load_and_chunk()
print(f"✅ Loaded {len(documents)} chunks.")

# ===============================
# 4. Initialize Pinecone
# ===============================
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = "hackrxvector"

if index_name not in [i.name for i in pc.list_indexes()]:
    pc.create_index(
        name=index_name,
        dimension=768,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )

index = pc.Index(index_name)

# ===============================
# 5. Upload to Pinecone
# ===============================
print("🚀 Uploading embeddings to Pinecone...")
vectorstore = PineconeVectorStore(index, embedding_model, text_key="text")
vectorstore.add_documents(documents)
print("✅ Upload completed and stored in Pinecone!")

# ===============================
# 6. RAG Query Functions
# ===============================
def retrieve_chunks(query, top_k=5):
    query_vector = embedding_model.embed_query(query)
    results = index.query(vector=query_vector, top_k=top_k, include_metadata=True)
    return [match["metadata"]["text"] for match in results["matches"]]

llm = GenerativeModel("gemini-2.5-pro")

import json

def ask_gemini(query):
    chunks = retrieve_chunks(query)
    context = "\n".join(chunks)

    prompt = f"""
    You are an insurance Expert. 
    Analyze the user's query using ONLY the given policy context and respond strictly in the following JSON format:

    {{
      "Decision": "approved" or "rejected",
      "Amount": "<approved amount or null>",
      "Justification": "<short reason for the decision>",
      "Clauses": ["<relevant clause 1>", "<relevant clause 2>"]
    }}

    Rules:
    - Do not include any text outside the JSON.
    - Justification must be under 15 words.
    - Clauses must be direct quotes from the context.

    Context:
    {context}

    Query: "{query}"
    """

    response = llm.generate_content(prompt).text.strip()

    # ✅ Parse JSON safely
    try:
        decision_json = json.loads(response)
    except json.JSONDecodeError:
        # If Gemini adds extra text, try to extract JSON using regex
        import re
        match = re.search(r"\{.*\}", response, re.DOTALL)
        if match:
            decision_json = json.loads(match.group(0))
        else:
            decision_json = {"error": "Invalid JSON response", "raw": response}

    return decision_json
