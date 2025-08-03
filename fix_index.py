import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from pipeline import process_uploaded_docs, GeminiEmbeddings, get_embedding_dimension

# ✅ Load environment variables
load_dotenv()

# ✅ Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = "hackrxvector-1"

# ✅ Initialize Gemini embedding model
embedding_model = GeminiEmbeddings()
expected_dim = get_embedding_dimension(embedding_model)

# ✅ 1. Delete old index if it exists
if any(i.name == index_name for i in pc.list_indexes()):
    print(f"⚠️ Deleting old index '{index_name}' to remove dimension mismatch...")
    pc.delete_index(index_name)

# ✅ 2. Recreate index with correct dimension
print(f"✅ Creating new index '{index_name}' with dimension {expected_dim}...")
pc.create_index(
    name=index_name,
    dimension=expected_dim,
    metric="cosine",
    spec=ServerlessSpec(cloud="aws", region="us-east-1")
)

print("✅ Index created successfully!")

# ✅ 3. Upload new default document
default_docs = [
    r"C:\Users\Priyanka Shahani\OneDrive\Desktop\HackRx\documents\Arogya Sanjeevani Policy - CIN - U10200WB1906GOI001713 1.pdf"
]

print("📤 Uploading default document to Pinecone...")
process_uploaded_docs(default_docs, namespace="default")

print("🎯 All steps completed successfully! The index now has only 768-d vectors.")
