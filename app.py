from fastapi import FastAPI, Request, HTTPException
import uvicorn
import logging
from claim_process import process_claim
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Insurance Query API", version="1.0.0")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Insurance Query API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Check if required environment variables are set
        gemini_key = os.getenv("GEMINI_API_KEY")
        pinecone_key = os.getenv("PINECONE_API_KEY")
        
        return {
            "status": "healthy",
            "gemini_configured": bool(gemini_key),
            "pinecone_configured": bool(pinecone_key),
            "message": "API is ready to process queries"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.post("/query")
async def handle_query(request: Request):
    """Process insurance queries"""
    try:
        logger.info("Received query request")
        
        # Parse JSON body
        data = await request.json()
        query = data.get("query", "")
        
        if not query:
            raise HTTPException(status_code=400, detail="Query field is required")
        
        logger.info(f"Processing query: {query[:100]}...")
        
        # Process the claim
        decision_json = process_claim(query)
        
        logger.info("Query processed successfully")
        return decision_json
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
