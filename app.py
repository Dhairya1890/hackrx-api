from fastapi import FastAPI, Request
import uvicorn
from claim_process import process_claim

app = FastAPI()

@app.post("/query")
async def handle_query(request: Request):
    data = await request.json()
    query = data.get("query", "")
    decision_json = process_claim(query)
    return decision_json

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
