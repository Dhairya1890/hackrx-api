import os
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader, TextLoader
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from langchain.embeddings.base import Embeddings
import google.generativeai as genai
from google.generativeai import GenerativeModel

load_dotenv()

# ✅ Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
llm = GenerativeModel("gemini-2.5-pro")

class GeminiEmbeddings(Embeddings):
    def embed_query(self, text: str):
        return genai.embed_content(model="embedding-001", content=text)["embedding"]

    def embed_documents(self, texts):
        return [self.embed_query(t) for t in texts]

# ✅ Pinecone Setup
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
embedding_model = GeminiEmbeddings()

# ✅ Process uploaded documents
def process_uploaded_docs(file_paths, namespace="default"):
    all_docs = []
    for path in file_paths:
        if path.endswith(".pdf"):
            loader = PyPDFLoader(path)
        else:
            loader = TextLoader(path)
        docs = loader.load()
        all_docs.extend(docs)

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_documents(all_docs)

    vectorstore = PineconeVectorStore(index, embedding_model, text_key="text", namespace=namespace)
    vectorstore.add_documents(chunks)
    print(f"✅ Uploaded {len(chunks)} chunks to Pinecone namespace: {namespace}")

# ✅ Retrieve relevant chunks
def retrieve_chunks(query, namespace="default", top_k=5):
    query_vector = embedding_model.embed_query(query)
    results = index.query(namespace=namespace, vector=query_vector, top_k=top_k, include_metadata=True)
    return [match["metadata"]["text"] for match in results["matches"]]

# ✅ Process claim with context
def process_claim(query, namespace="default"):
    chunks = retrieve_chunks(query, namespace=namespace)
    context = "\n".join(chunks)

    prompt = f"""
    You are an insurance Expert. Use ONLY the following context to answer the question.

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

    response = llm.generate_content(prompt).text.strip()
    return response  # should be valid JSON
