from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Header
from fastapi.responses import JSONResponse
import uvicorn
import logging
import os
import requests
from dotenv import load_dotenv
from claim_process import process_claim, process_uploaded_docs
import tempfile
import shutil

# Load environment variables
load_dotenv()

WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://eos5psqf4l1yvrg.m.pipedream.net")
EXPECTED_BEARER = os.getenv("TEAM_BEARER_TOKEN")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Insurance Query API", version="2.0.0")

# ✅ Health Check Endpoints
@app.get("/")
async def root():
    return {"message": "Insurance Query API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Background processing enabled"}


# ✅ Helper: Authentication
def check_auth(authorization: str):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split(" ")[1]
    if token != EXPECTED_BEARER:
        raise HTTPException(status_code=401, detail="Unauthorized")


# ✅ Background Task to Process
def background_processing(query, file_url, namespace):
    try:
        # If file_url is provided, download and process it
        file_paths = []
        if file_url:
            tmp_dir = tempfile.mkdtemp()
            local_path = os.path.join(tmp_dir, "uploaded_doc.pdf")
            r = requests.get(file_url, stream=True)
            with open(local_path, "wb") as f:
                shutil.copyfileobj(r.raw, f)
            file_paths.append(local_path)
            process_uploaded_docs(file_paths, namespace=namespace)

        # Process query with pipeline
        decision_json = process_claim(query, namespace=namespace)

        # Send to webhook when complete
        requests.post(WEBHOOK_URL, json=decision_json)
        logger.info("✅ Sent results to webhook")

    except Exception as e:
        logger.error(f"Background processing failed: {e}")
        requests.post(WEBHOOK_URL, json={"error": str(e)})


# ✅ Main API Endpoint
@app.post("/api/v1/hackrx/run")
async def run_hackrx(request: Request, background_tasks: BackgroundTasks, authorization: str = Header(None)):
    # 🔐 Authenticate
    check_auth(authorization)

    try:
        data = await request.json()
        query = data.get("questions", [])
        file_url = data.get("documents")
        namespace = "session1"  # Could also be dynamic

        if not query:
            raise HTTPException(status_code=400, detail="Questions are required")

        # ✅ Start background task
        background_tasks.add_task(background_processing, query, file_url, namespace)

        # ✅ Return immediate response
        return JSONResponse(
            status_code=200,
            content={"status": "processing", "message": "Document and queries are being processed."}
        )

    except Exception as e:
        logger.error(f"Request failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
