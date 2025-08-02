import os
import re
import json
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader, TextLoader
import google.generativeai as genai
from langchain.embeddings.base import Embeddings

# 🔹 Load environment variables
load_dotenv()

# ✅ Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ✅ Gemini Embeddings Class
class GeminiEmbeddings(Embeddings):
    def embed_query(self, text: str):
        return genai.embed_content(model="embedding-001", content=text)["embedding"]
    
    def embed_documents(self, texts):
        return [self.embed_query(t) for t in texts]

# ✅ Initialize LLM
llm = genai.GenerativeModel("gemini-2.5-pro")

# ✅ Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = "hackrxvector"

# ✅ Detect embedding dimension dynamically
def get_embedding_dimension(embedding_model):
    test_vec = embedding_model.embed_query("test")
    return len(test_vec)

embedding_model = GeminiEmbeddings()
expected_dim = get_embedding_dimension(embedding_model)

# ✅ Safe Index Check (No auto-delete)
index_exists = any(i.name == index_name for i in pc.list_indexes())
if index_exists:
    stats = pc.describe_index(index_name)
    current_dim = getattr(stats, 'dimension', None)
    if current_dim and current_dim != expected_dim:
        print(f"🚨 Dimension mismatch! Index={current_dim}, Expected={expected_dim}.")
        print("❗ Please delete and recreate the index manually.")
else:
    pc.create_index(
        name=index_name,
        dimension=expected_dim,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
    print(f"✅ Created Pinecone index '{index_name}' with dimension {expected_dim}")

# ✅ Connect to Pinecone Index
index = pc.Index(index_name)

# ======================================================
# 📌 DOCUMENT HANDLING
# ======================================================
def namespace_exists(namespace: str) -> bool:
    stats = index.describe_index_stats()
    return stats["namespaces"].get(namespace, {}).get("vector_count", 0) > 0

def process_uploaded_docs(file_paths, namespace="default"):
    """Load, chunk, embed, and store documents in Pinecone."""
    if namespace_exists(namespace):
        print(f"ℹ️ Namespace '{namespace}' already has data. Skipping embedding.")
        return

    all_docs = []
    for path in file_paths:
        loader = PyPDFLoader(path) if path.endswith(".pdf") else TextLoader(path)
        docs = loader.load()
        all_docs.extend(docs)

    # Chunk the documents
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_documents(all_docs)

    # Upload to Pinecone
    vectorstore = PineconeVectorStore(index, embedding_model, text_key="text", namespace=namespace)
    vectorstore.add_documents(chunks)
    print(f"✅ Uploaded {len(chunks)} chunks to Pinecone namespace '{namespace}'")

# ======================================================
# 📌 RETRIEVAL
# ======================================================
def retrieve_chunks(query, namespace="default", top_k=5):
    """Retrieve top-k relevant chunks for a query."""
    query_vector = embedding_model.embed_query(query)
    results = index.query(namespace=namespace, vector=query_vector, top_k=top_k, include_metadata=True)
    return [match["metadata"]["text"] for match in results["matches"]]

# ======================================================
# 📌 CLAIM PROCESSING (RAG + Gemini)
# ======================================================
def process_claim(query, namespace="default"):
    """Retrieve context from Pinecone and ask Gemini to return decision JSON."""
    chunks = retrieve_chunks(query, namespace=namespace)
    context = "\n".join(chunks)

    prompt = f"""
    You are an insurance Expert. Use ONLY the provided context to answer.

    Context:
    {context}

    Query: {query}

    Respond strictly in valid JSON:
    {{
      "Decision": "approved" or "rejected",
      "Amount": "<approved amount or null>",
      "Justification": "<short reason>",
      "Clauses": ["<clause1>", "<clause2>"]
    }}
    """

    raw_response = llm.generate_content(prompt).text.strip()
    cleaned = re.sub(r"```json|```", "", raw_response).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON from model", "raw_response": raw_response}
