import os
from pinecone import Pinecone, ServerlessSpec
from pipeline import process_uploaded_docs, get_embedding_dimension, GeminiEmbeddings
from dotenv import load_dotenv

# Load API keys
load_dotenv()

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = "hackrxvector"

# Initialize embedding model
embedding_model = GeminiEmbeddings()
expected_dim = get_embedding_dimension(embedding_model)

# ✅ Step 1: Delete existing index (if exists)
if any(i.name == index_name for i in pc.list_indexes()):
    print(f"⚠️ Deleting old index '{index_name}' due to dimension mismatch...")
    pc.delete_index(index_name)

# ✅ Step 2: Recreate index with correct dimension
print(f"✅ Creating index '{index_name}' with dimension {expected_dim}")
pc.create_index(
    name=index_name,
    dimension=expected_dim,
    metric="cosine",
    spec=ServerlessSpec(cloud="aws", region="us-east-1")
)

# ✅ Step 3: Upload new documents
# Provide your new document path(s) here
docs = [r"C:\Users\Priyanka Shahani\OneDrive\Desktop\HackRx\documents\BAJHLIP23020V012223.pdf"]

print("📤 Uploading documents...")
process_uploaded_docs(docs, namespace="default")

print("✅ Index reset and document embedding completed successfully!")
