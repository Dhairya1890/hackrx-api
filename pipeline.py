import os
import json
import re
import logging
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader, TextLoader
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
import google.generativeai as genai
from langchain.embeddings.base import Embeddings

# ✅ Load environment variables
load_dotenv()

# ✅ Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Google Gemini setup
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ✅ Custom Gemini Embeddings Wrapper
class GeminiEmbeddings(Embeddings):
    def embed_query(self, text: str):
        return genai.embed_content(model="models/embedding-001", content=text)["embedding"]

    def embed_documents(self, texts):
        return [self.embed_query(t) for t in texts]


embedding_model = GeminiEmbeddings()

# ✅ Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = "hackrxvector"

# Recreate index if dimension mismatch happens
def ensure_index():
    existing = [i.name for i in pc.list_indexes()]
    if index_name in existing:
        stats = pc.describe_index(index_name)
        if stats.dimension != 1536:
            logger.warning("⚠️ Dimension mismatch detected. Recreating index...")
            pc.delete_index(index_name)
    if index_name not in [i.name for i in pc.list_indexes()]:
        pc.create_index(
            name=index_name,
            dimension=1536,  # ✅ Gemini embeddings return 1536 dimensions
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )

ensure_index()
index = pc.Index(index_name)


# ✅ Helper: Check if namespace already has vectors
def namespace_exists(namespace: str) -> bool:
    stats = index.describe_index_stats()
    return stats["namespaces"].get(namespace, {}).get("vector_count", 0) > 0


# ✅ Process uploaded documents
def process_uploaded_docs(file_paths, namespace="default"):
    """
    Loads, chunks, embeds, and stores documents in Pinecone.
    Always refreshes namespace to avoid stale data during judging.
    """
    logger.info(f"📄 Processing documents for namespace '{namespace}'")

    # Clear old namespace
    try:
        index.delete(delete_all=True, namespace=namespace)
        logger.info(f"🗑️ Cleared namespace '{namespace}'")
    except Exception as e:
        logger.warning(f"⚠️ Failed to clear namespace '{namespace}': {e}")

    # Load and chunk documents
    all_docs = []
    for path in file_paths:
        loader = PyPDFLoader(path) if path.endswith(".pdf") else TextLoader(path)
        all_docs.extend(loader.load())

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_documents(all_docs)

    # Embed & upload
    vectorstore = PineconeVectorStore(index, embedding_model, text_key="text", namespace=namespace)
    vectorstore.add_documents(chunks)
    logger.info(f"✅ Uploaded {len(chunks)} chunks into namespace '{namespace}'")


# ✅ Retrieve relevant chunks for a query
def retrieve_chunks(query, namespace="default", top_k=5):
    query_vector = embedding_model.embed_query(query)
    results = index.query(namespace=namespace, vector=query_vector, top_k=top_k, include_metadata=True)
    return [match["metadata"]["text"] for match in results.get("matches", [])]


# ✅ LLM Setup
llm = genai.GenerativeModel("gemini-2.5-pro")


# ✅ Process a single claim query
def process_claim(query, namespace="default"):
    """
    Retrieves context and asks Gemini to produce a decision in JSON format.
    """
    logger.info(f"🔍 Retrieving chunks for query: {query}")
    chunks = retrieve_chunks(query, namespace=namespace)

    if not chunks:
        return {"error": "No relevant context found"}

    context = "\n".join(chunks)

    prompt = f"""
    You are an insurance Expert. Use ONLY the given policy context to answer.

    Context:
    {context}

    Query: {query}

    Respond strictly in JSON format:
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
        logger.warning("⚠️ Model returned invalid JSON, returning raw text")
        return {"raw_response": raw_response}
