from fastapi import FastAPI, Request, UploadFile, Form, BackgroundTasks, HTTPException
import uvicorn
import logging
import os
import requests
from dotenv import load_dotenv
from claim_process import process_claim, process_uploaded_docs

# Load environment variables
load_dotenv()
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://eos5psqf4l1yvrg.m.pipedream.net")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Insurance Query API", version="1.1.0")

# ✅ Health Check
@app.get("/")
async def root():
    return {"status": "healthy", "message": "Insurance Query API is running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "gemini": bool(os.getenv("GEMINI_API_KEY")),
        "pinecone": bool(os.getenv("PINECONE_API_KEY")),
    }

# ✅ Background worker for embedding
def background_embedding(file_paths, namespace):
    try:
        process_uploaded_docs(file_paths, namespace=namespace)
        logger.info(f"✅ Finished processing docs for namespace={namespace}")
    except Exception as e:
        logger.error(f"❌ Background embedding failed: {e}")

# ✅ Upload + Query in one endpoint
@app.post("/query")
async def handle_query(
    background_tasks: BackgroundTasks,
    query: str = Form(...),
    session_id: str = Form("default"),
    files: list[UploadFile] = None
):
    try:
        namespace = session_id
        file_paths = []

        # ✅ If files are provided, save temporarily and process in background
        if files:
            os.makedirs("uploaded_docs", exist_ok=True)
            for file in files:
                save_path = f"uploaded_docs/{file.filename}"
                with open(save_path, "wb") as f:
                    f.write(await file.read())
                file_paths.append(save_path)

            logger.info(f"Received {len(file_paths)} files. Starting background embedding.")
            background_tasks.add_task(background_embedding, file_paths, namespace)

        # ✅ Process query (retrieves from Pinecone)
        logger.info(f"Processing query: {query[:80]}...")
        decision_json = process_claim(query, namespace=namespace)

        # ✅ Send to webhook asynchronously
        try:
            requests.post(WEBHOOK_URL, json={"query": query, "response": decision_json})
        except Exception as werr:
            logger.warning(f"Webhook send failed: {werr}")

        return {"status": "processing_docs" if files else "success", "decision": decision_json}

    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
