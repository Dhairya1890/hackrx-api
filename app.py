from fastapi import FastAPI, Request, HTTPException
import uvicorn
import logging
import requests
import os
from dotenv import load_dotenv
from claim_process import process_claim

# Load environment variables
load_dotenv()

WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://eos5psqf4l1yvrg.m.pipedream.net")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Insurance Query API", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "Insurance Query API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    try:
        gemini_key = os.getenv("GEMINI_API_KEY")
        pinecone_key = os.getenv("PINECONE_API_KEY")
        return {
            "status": "healthy",
            "gemini_configured": bool(gemini_key),
            "pinecone_configured": bool(pinecone_key)
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {e}")

@app.post("/query")
async def handle_query(request: Request):
    try:
        data = await request.json()
        query = data.get("query")
        if not query:
            raise HTTPException(status_code=400, detail="Query field is required")

        logger.info(f"Processing query: {query[:100]}...")

        # Process the claim (calls your pipeline)
        decision_json = process_claim(query)

        # Send decision to webhook
        try:
            requests.post(WEBHOOK_URL, json=decision_json)
            logger.info("✅ Decision sent to webhook")
        except Exception as webhook_err:
            logger.error(f"Webhook send failed: {webhook_err}")

        return {"status": "success", "decision": decision_json}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
