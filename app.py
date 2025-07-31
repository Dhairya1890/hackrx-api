from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import logging
import requests
import os
from dotenv import load_dotenv
from pipeline import process_claim, process_uploaded_docs

# ✅ Load environment variables
load_dotenv()

WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://eos5psqf4l1yvrg.m.pipedream.net")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Insurance Query API", version="2.0.0")

# ✅ Health Check Endpoints
@app.get("/")
async def root():
    return {"message": "Insurance Query API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    try:
        return {
            "status": "healthy",
            "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
            "pinecone_configured": bool(os.getenv("PINECONE_API_KEY"))
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed: {e}")

# ✅ Query + Optional Document Upload
@app.post("/query")
async def handle_query(query: str = Form(...), session_id: str = Form("default"), files: list[UploadFile] = File(None)):
    try:
        file_paths = []

        # ✅ Case 1 & 3: User uploads new docs
        if files:
            os.makedirs("uploads", exist_ok=True)
            for f in files:
                file_path = f"uploads/{f.filename}"
                with open(file_path, "wb") as out:
                    out.write(await f.read())
                file_paths.append(file_path)
            process_uploaded_docs(file_paths, namespace=session_id)
            logger.info(f"Docs processed for session {session_id}")
        else:
            logger.info(f"No new documents uploaded, using existing namespace: {session_id}")

        # ✅ Process claim with namespace
        decision_json = process_claim(query, namespace=session_id)

        # ✅ Send decision to external webhook
        try:
            requests.post(WEBHOOK_URL, json=decision_json)
        except Exception as e:
            logger.error(f"Webhook send failed: {e}")

        return JSONResponse(content={"status": "success", "decision": decision_json})

    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
