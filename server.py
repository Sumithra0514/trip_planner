
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
from backend import run

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent

class TravelRequest(BaseModel):
    query: str

@app.get("/")
def home():
    return FileResponse(BASE_DIR / "index.html")

@app.post("/plan-trip")
def plan_trip(request: TravelRequest):
    try:
        result = run(request.query)
        return {"answer": result["answer"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
