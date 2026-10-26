
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend import run

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Local testing only
    allow_methods=["*"],
    allow_headers=["*"],
)


class TravelRequest(BaseModel):
    query: str


@app.post("/plan-trip")
def plan_rip(request: TravelRequest):

    try:
        result =  run(request.query)

        return {"answer": result["answer"]}

    except Exception as e:
        print("ERROR:", repr(e))
        raise
