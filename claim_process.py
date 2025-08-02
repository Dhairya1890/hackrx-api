import os
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader, TextLoader
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from pipeline import GeminiEmbeddings, llm

load_dotenv()

# ✅ Pinecone Setup
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = "hackrxvector"

# Create index if not exists
if index_name not in [i.name for i in pc.list_indexes()]:
    pc.create_index(
        name=index_name,
        dimension=768,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )

index = pc.Index(index_name)
embedding_model = GeminiEmbeddings()


# ✅ Helper: Check if namespace already has data
def namespace_exists(namespace: str) -> bool:
    stats = index.describe_index_stats()
    return stats["namespaces"].get(namespace, {}).get("vector_count", 0) > 0


# ✅ Process uploaded documents
def process_uploaded_docs(file_paths, namespace="default"):
    """
    Loads, chunks, embeds, and stores documents in Pinecone.
    Skips processing if namespace already exists.
    """
    if namespace_exists(namespace):
        print(f"ℹ️ Namespace '{namespace}' already has data. Skipping embedding.")
        return

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
    """
    Retrieves relevant context from Pinecone and asks Gemini for structured decision.
    """
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
    return response
