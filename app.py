from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form
import uvicorn
import logging
import os
import requests
import json
import re
from dotenv import load_dotenv
from claim_process import process_claim, process_uploaded_docs

# ✅ Load environment variables
load_dotenv()

# ✅ Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Insurance Query API", version="2.0.0")

WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://eos5psqf4l1yvrg.m.pipedream.net")

# ✅ Health Check
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
        raise HTTPException(status_code=500, detail=f"Health check failed: {e}")


# ✅ Existing Endpoint: /query (Manual file upload & single query)
@app.post("/query")
async def handle_query(
    query: str = Form(...),
    session_id: str = Form("default"),
    files: list[UploadFile] = None
):
    try:
        # 🔹 If files are uploaded, process and embed them
        if files:
            file_paths = []
            for file in files:
                path = f"/tmp/{file.filename}"
                with open(path, "wb") as f:
                    f.write(await file.read())
                file_paths.append(path)
            process_uploaded_docs(file_paths, namespace=session_id)

        # 🔹 Process the query
        decision_json = process_claim(query, namespace=session_id)

        # 🔹 Send to webhook (optional)
        try:
            requests.post(WEBHOOK_URL, json=decision_json, timeout=5)
        except Exception as webhook_err:
            logger.warning(f"Webhook send failed: {webhook_err}")

        return {"status": "success", "decision": decision_json}

    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


# ✅ Judges’ Endpoint: /hackrx/run (Remote PDF + Multiple Questions)
@app.post("/hackrx/run")
async def hackrx_run(request: Request):
    try:
        body = await request.json()
        document_url = body.get("documents")
        questions = body.get("questions", [])

        if not document_url:
            raise HTTPException(status_code=400, detail="Document URL is required")
        if not questions:
            raise HTTPException(status_code=400, detail="Questions list is required")

        # 🔹 Download the provided PDF to /tmp
        file_path = "/tmp/policy.pdf"
        try:
            r = requests.get(document_url, timeout=30)
            r.raise_for_status()
            with open(file_path, "wb") as f:
                f.write(r.content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to download document: {e}")

        # 🔹 Embed document into default namespace (overwriting old one)
        process_uploaded_docs([file_path], namespace="default")

        # 🔹 Process each question and extract a clean text answer
        results = []
        for q in questions:
            raw_answer = process_claim(q, namespace="default")

            # 🟢 Extract clean text from JSON or string
            if isinstance(raw_answer, dict):
                clean_answer = raw_answer.get("Justification", json.dumps(raw_answer))
            else:
                match = re.search(r'"Justification"\s*:\s*"([^"]+)"', str(raw_answer))
                clean_answer = match.group(1) if match else str(raw_answer)

            results.append(clean_answer)

        # ✅ Return in required format
        return {"answers": results}

    except Exception as e:
        logger.error(f"/hackrx/run failed: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


# ✅ Run locally
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
