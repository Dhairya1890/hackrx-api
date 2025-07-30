import os
import json
import google.generativeai as genai
from pinecone import Pinecone
from langchain.vectorstores import Pinecone as PineconeStore
from langchain.schema import Document

# 🔹 Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# 🔹 Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = "hackrxvector"
index = pc.Index(index_name)

# 🔹 Gemini wrapper for embeddings
from langchain.embeddings.base import Embeddings

class GeminiEmbeddings(Embeddings):
    def embed_query(self, text: str):
        return genai.embed_content(model="embedding-001", content=text)["embedding"]

    def embed_documents(self, texts):
        return [self.embed_query(t) for t in texts]

embedding_model = GeminiEmbeddings()


# 🔹 Retrieve relevant chunks
def retrieve_chunks(query, top_k=5):
    query_vector = embedding_model.embed_query(query)
    results = index.query(vector=query_vector, top_k=top_k, include_metadata=True)
    return [match["metadata"]["text"] for match in results["matches"]]


# 🔹 Ask Gemini to generate decision
def ask_gemini(query: str):
    from google.generativeai import GenerativeModel
    llm = GenerativeModel("gemini-2.5-pro")

    chunks = retrieve_chunks(query)
    context = "\n".join(chunks)

    prompt = f"""
    You are an insurance Expert.
    Analyze the user's query using ONLY the given policy context and respond strictly in this JSON:

    {{
      "Decision": "approved" or "rejected",
      "Amount": "<approved amount or null>",
      "Justification": "<short reason for the decision>",
      "Clauses": ["<relevant clause 1>", "<relevant clause 2>"]
    }}

    Context:
    {context}

    Query: "{query}"
    """

    response = llm.generate_content(prompt)
    return response.text.strip()


# 🔹 Main function to be used by FastAPI
def process_claim(query: str):
    decision = ask_gemini(query)
    try:
        return json.loads(decision)   # Ensure valid JSON
    except:
        return {"error": "Invalid JSON from Gemini", "raw": decision}
