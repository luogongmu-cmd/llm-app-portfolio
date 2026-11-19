from fastapi import FastAPI
from pydantic import BaseModel

from agent_loop import run

app = FastAPI(title="kb-agent")


class Ask(BaseModel):
    question: str


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/chat")
def chat(req: Ask):
    return {"answer": run(req.question)}