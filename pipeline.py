import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader, TextLoader
import google.generativeai as genai
from langchain.embeddings.base import Embeddings

load_dotenv()

# ✅ Define Gemini Embeddings Here
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class GeminiEmbeddings(Embeddings):
    def embed_query(self, text: str):
        return genai.embed_content(model="embedding-001", content=text)["embedding"]
    
    def embed_documents(self, texts):
        return [self.embed_query(t) for t in texts]

# ✅ Initialize LLM Here
llm = genai.GenerativeModel("gemini-2.5-pro")

# ✅ Then continue with Pinecone setup and rest of code...
