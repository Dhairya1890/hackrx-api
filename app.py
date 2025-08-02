from fastapi import FastAPI, Request, UploadFile, File, Form, BackgroundTasks, HTTPException
import uvicorn
import logging
import os
import requests
from dotenv import load_dotenv
from claim_process import process_claim, process_uploaded_docs

load_dotenv()

WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://eos5psqf4l1yvrg.m.pipedream.net")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Insurance Query API", version="1.1.0")

# ✅ Background worker to handle processing
def background_process(query: str, files: list, session_id: str):
    try:
        namespace = session_id or "default"

        # ✅ Step 1: If files are uploaded, save & embed
        if files:
            file_paths = []
            for uploaded in files:
                path = f"/tmp/{uploaded.filename}"
                with open(path, "wb") as f:
                    f.write(uploaded.file.read())
                file_paths.append(path)

            process_uploaded_docs(file_paths, namespace=namespace)

        # ✅ Step 2: Process claim
        decision_json = process_claim(query, namespace=namespace)

        # ✅ Step 3: Send result to webhook
        requests.post(WEBHOOK_URL, json=decision_json)
        logger.info("✅ Process completed and sent to webhook")

    except Exception as e:
        logger.error(f"Background processing failed: {e}")


@app.get("/")
async def root():
    return {"message": "Insurance Query API is running", "status": "healthy"}


@app.post("/query")
async def handle_query(
    background_tasks: BackgroundTasks,
    query: str = Form(...),
    session_id: str = Form("default"),
    files: list[UploadFile] = File(default=[])
):
    try:
        logger.info(f"📥 Received query: {query[:100]}...")
        background_tasks.add_task(background_process, query, files, session_id)

        return {"status": "processing", "message": "Your request is being processed asynchronously."}

    except Exception as e:
        logger.error(f"❌ Query handling failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/hackrx/run")
async def hackrx_run(request: Request, background_tasks: BackgroundTasks):
    """
    Judges will hit this endpoint with a JSON payload:
    {
      "documents": "<url>",
      "questions": ["Q1", "Q2"]
    }
    """
    try:
        data = await request.json()
        doc_url = data.get("documents")
        questions = data.get("questions", [])
        namespace = "judge-doc"

        if doc_url:
            # ✅ Download the document temporarily
            file_path = "/tmp/judge_policy.pdf"
            resp = requests.get(doc_url)
            with open(file_path, "wb") as f:
                f.write(resp.content)

            # ✅ Embed document asynchronously
            background_tasks.add_task(process_uploaded_docs, [file_path], namespace)

        # ✅ Process questions asynchronously
        for q in questions:
            background_tasks.add_task(background_process, q, [], namespace)

        return {"status": "processing", "message": "Document and queries are being processed."}

    except Exception as e:
        logger.error(f"❌ HackRx run failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
