import os
import json
import logging
import google.generativeai as genai
from pinecone import Pinecone
from langchain.vectorstores import Pinecone as PineconeStore
from langchain.schema import Document

# Configure logging
logger = logging.getLogger(__name__)

# 🔹 Configure Gemini
try:
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")
    genai.configure(api_key=gemini_api_key)
    logger.info("Gemini configured successfully")
except Exception as e:
    logger.error(f"Failed to configure Gemini: {str(e)}")
    raise

# 🔹 Initialize Pinecone
try:
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    if not pinecone_api_key:
        raise ValueError("PINECONE_API_KEY environment variable is not set")
    
    pc = Pinecone(api_key=pinecone_api_key)
    index_name = "hackrxvector"
    index = pc.Index(index_name)
    logger.info("Pinecone initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Pinecone: {str(e)}")
    raise

# 🔹 Gemini wrapper for embeddings
from langchain.embeddings.base import Embeddings

class GeminiEmbeddings(Embeddings):
    def embed_query(self, text: str):
        try:
            return genai.embed_content(model="embedding-001", content=text)["embedding"]
        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            raise

    def embed_documents(self, texts):
        return [self.embed_query(t) for t in texts]

embedding_model = GeminiEmbeddings()

# 🔹 Retrieve relevant chunks
def retrieve_chunks(query, top_k=5):
    try:
        logger.info(f"Retrieving chunks for query: {query[:50]}...")
        query_vector = embedding_model.embed_query(query)
        results = index.query(vector=query_vector, top_k=top_k, include_metadata=True)
        chunks = [match["metadata"]["text"] for match in results["matches"]]
        logger.info(f"Retrieved {len(chunks)} chunks")
        return chunks
    except Exception as e:
        logger.error(f"Failed to retrieve chunks: {str(e)}")
        raise

# 🔹 Ask Gemini to generate decision
def ask_gemini(query: str):
    try:
        from google.generativeai import GenerativeModel
        llm = GenerativeModel("gemini-2.0-flash-exp")

        chunks = retrieve_chunks(query)
        context = "\n".join(chunks)

        prompt = f"""
        You are an insurance Expert.
        Analyze the user's query using ONLY the given policy context and respond with ONLY a valid JSON object (no markdown, no code blocks):

        {{
          "Decision": "approved" or "rejected",
          "Amount": "<approved amount or null>",
          "Justification": "<short reason for the decision>",
          "Clauses": ["<relevant clause 1>", "<relevant clause 2>"]
        }}

        Context:
        {context}

        Query: "{query}"

        Respond with ONLY the JSON object, no additional text or formatting.
        """

        logger.info("Generating response with Gemini...")
        response = llm.generate_content(prompt)
        logger.info("Gemini response generated successfully")
        return response.text.strip()
    except Exception as e:
        logger.error(f"Failed to generate Gemini response: {str(e)}")
        raise

# 🔹 Main function to be used by FastAPI
def process_claim(query: str):
    try:
        logger.info(f"Processing claim query: {query[:50]}...")
        decision = ask_gemini(query)
        try:
            # Clean up Gemini's response - remove markdown code blocks if present
            cleaned_response = decision.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]  # Remove ```json
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]  # Remove ```
            cleaned_response = cleaned_response.strip()
            
            parsed_decision = json.loads(cleaned_response)
            logger.info("Successfully parsed JSON response")
            return parsed_decision
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            logger.error(f"Raw response: {decision}")
            return {"error": "Invalid JSON from Gemini", "raw": decision}
    except Exception as e:
        logger.error(f"Claim processing failed: {str(e)}")
        return {"error": f"Processing failed: {str(e)}"}
