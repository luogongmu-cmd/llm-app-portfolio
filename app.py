import json

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agent_graph import GRAPH
from agent_graph import run as run_graph
from agent_loop import run as run_handwritten

app = FastAPI(title="kb-agent")


class Ask(BaseModel):
    question: str


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/chat")
def chat(req: Ask):
    """LangGraph 版（第 1–2 周）。"""
    return {"answer": run_graph(req.question)}


@app.post("/chat/handwritten")
def chat_handwritten(req: Ask):
    """手写循环版（Day5），保留作对照。"""
    return {"answer": run_handwritten(req.question)}


@app.post("/chat/stream")
def chat_stream(req: Ask):
    """SSE：逐节点推送 plan / retrieve / reflect / answer。"""
    def gen():
        for event in GRAPH.stream({"question": req.question, "rounds": 0}, stream_mode="updates"):
            for node, update in event.items():
                payload = {"node": node}
                if isinstance(update, dict):
                    if "rounds" in update:
                        payload["rounds"] = update["rounds"]
                    if "hits" in update:
                        payload["hits"] = len(update["hits"])
                    if update.get("error"):
                        payload["error"] = update["error"]
                    if "answer" in update:
                        payload["answer"] = update["answer"]
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache"})
