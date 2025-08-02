import os
import logging
import requests
from fastapi import FastAPI, Request, HTTPException, Header
from dotenv import load_dotenv
from pipeline import process_uploaded_docs, process_claim  # ✅ using your pipeline functions

load_dotenv()

# 🔹 Load expected Bearer token from environment
EXPECTED_BEARER = os.getenv("TEAM_BEARER_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="HackRx LLM Retrieval API", version="2.0.0")


# ✅ Root & Health Check
@app.get("/")
async def root():
    return {"message": "HackRx Retrieval API is running", "status": "healthy"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API ready"}


# ✅ 🔥 Main Endpoint required by HackRx: /api/v1/hackrx/run
@app.post("/api/v1/hackrx/run")
async def hackrx_run(request: Request, authorization: str = Header(None)):
    try:
        # 🔹 Step 1: Authenticate using Bearer token
        if authorization != f"Bearer {EXPECTED_BEARER}":
            logger.warning("Unauthorized request detected")
            raise HTTPException(status_code=401, detail="Unauthorized")

        # 🔹 Step 2: Parse incoming JSON
        data = await request.json()
        document_url = data.get("documents")
        questions = data.get("questions", [])

        if not document_url or not questions:
            raise HTTPException(status_code=400, detail="Missing 'documents' or 'questions' field")

        # 🔹 Step 3: Download document
        local_path = "/tmp/policy.pdf"
        try:
            resp = requests.get(document_url, timeout=20)
            with open(local_path, "wb") as f:
                f.write(resp.content)
            logger.info(f"Downloaded document from {document_url}")
        except Exception as e:
            logger.error(f"Failed to download document: {e}")
            raise HTTPException(status_code=500, detail="Failed to download document")

        # 🔹 Step 4: Embed the document (new namespace for each request)
        namespace = "hackrx_test"
        process_uploaded_docs([local_path], namespace=namespace)

        # 🔹 Step 5: Process each question using RAG pipeline
        answers = []
        for q in questions:
            try:
                decision_json = process_claim(q, namespace=namespace)
                # Ensure proper string or dict output
                answers.append(decision_json if isinstance(decision_json, str) else str(decision_json))
            except Exception as e:
                answers.append(f"Error processing question: {str(e)}")

        # 🔹 Step 6: Return in required JSON format
        return {"answers": answers}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in /api/v1/hackrx/run: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")
