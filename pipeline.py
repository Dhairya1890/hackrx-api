import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore

load_dotenv()

# ✅ Pinecone Setup
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = "hackrxvector"

# ✅ Detect embedding dimension dynamically
def get_embedding_dimension(embedding_model):
    """Generate a dummy embedding to detect dimension."""
    test_vector = embedding_model.embed_query("test")
    return len(test_vector)

embedding_model = GeminiEmbeddings()
expected_dim = get_embedding_dimension(embedding_model)

# ✅ Check index dimension (Do NOT delete in production)
index_exists = any(i.name == index_name for i in pc.list_indexes())
if index_exists:
    stats = pc.describe_index(index_name)
    current_dim = getattr(stats, 'dimension', None)

    if current_dim and current_dim != expected_dim:
        # ❗ Just log warning, do not delete
        print(f"🚨 Dimension mismatch detected!")
        print(f"➡️ Index '{index_name}' uses {current_dim}, but embeddings expect {expected_dim}.")
        print("❗ Please recreate the index manually with the correct dimension.")
else:
    # ✅ Create index if missing
    pc.create_index(
        name=index_name,
        dimension=expected_dim,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
    print(f"✅ Created Pinecone index '{index_name}' with dimension {expected_dim}")

# ✅ Connect to index
index = pc.Index(index_name)
vectorstore = PineconeVectorStore(index, embedding_model, text_key="text")
