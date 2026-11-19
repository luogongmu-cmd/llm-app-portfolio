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


@app.get("/debug")
def debug():
    """临时诊断：确认索引是否可读（验证后删除）。"""
    import chromadb

    from query import search

    col = chromadb.PersistentClient(path=".chroma").get_or_create_collection("kb_day2")
    return {"count": col.count(), "hits": search("chunk_size")}