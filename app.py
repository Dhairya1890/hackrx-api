import os
import json
import logging
import requests
from fastapi import FastAPI, Request, HTTPException, Header
from dotenv import load_dotenv
from claim_process import process_uploaded_docs, process_claim  # ✅ use your existing pipeline functions

# ✅ Load environment variables
load_dotenv()

# ✅ Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Bearer Token from environment
EXPECTED_BEARER = os.getenv("TEAM_BEARER_TOKEN")  # <-- must match the one in judging system

app = FastAPI(title="HackRx Retrieval API", version="1.0.0")


# -------------------- AUTH CHECK -------------------- #
def verify_bearer(auth_header: str):
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = auth_header.split(" ")[1]
    if token != EXPECTED_BEARER:
        raise HTTPException(status_code=401, detail="Unauthorized")


# -------------------- HEALTH ENDPOINT -------------------- #
@app.get("/")
async def root():
    return {"message": "HackRx Retrieval API running", "status": "healthy"}


# -------------------- MAIN JUDGING ENDPOINT -------------------- #
@app.post("/api/v1/hackrx/run")
async def hackrx_run(request: Request, authorization: str = Header(None)):
    """
    Judges will POST here with:
    {
        "documents": "<PDF_URL>",
        "questions": ["q1", "q2", ...]
    }
    """
    # ✅ 1. Verify Bearer Authentication
    verify_bearer(authorization)

    try:
        # ✅ 2. Parse incoming JSON
        data = await request.json()
        pdf_url = data.get("documents")
        questions = data.get("questions", [])

        if not pdf_url or not questions:
            raise HTTPException(status_code=400, detail="Missing 'documents' or 'questions'")

        logger.info(f"📄 Downloading and processing document: {pdf_url}")

        # ✅ 3. Download the document to a temporary file
        local_pdf = "/tmp/input.pdf"
        r = requests.get(pdf_url)
        if r.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to download PDF from provided URL")
        with open(local_pdf, "wb") as f:
            f.write(r.content)

        # ✅ 4. Process document and index it
        process_uploaded_docs([local_pdf], namespace="judging")

        # ✅ 5. Process each question
        answers = []
        for q in questions:
            logger.info(f"🔍 Processing query: {q}")
            result = process_claim(q, namespace="judging")

            # result is already JSON → extract only justification text if needed
            if isinstance(result, dict) and "error" not in result:
                answers.append(result.get("Justification", json.dumps(result)))
            else:
                answers.append(json.dumps(result))

        # ✅ 6. Return final JSON in expected format
        return {"answers": answers}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
