"""FastAPI 服务：并发限制、超时/重试、缓存、幂等（request_id）与 /metrics。"""
import asyncio
import json
import time
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from agent_graph import GRAPH
from agent_graph import run as run_graph
from agent_loop import run as run_handwritten

app = FastAPI(title="kb-agent")

MAX_CONCURRENCY = 4
CACHE_TTL = 60

_executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENCY)
_sem = asyncio.Semaphore(MAX_CONCURRENCY)
_cache: dict[str, tuple[float, str]] = {}
_metrics = {"requests": 0, "errors": 0, "cache_hits": 0, "total_ms": 0.0}


class Ask(BaseModel):
    question: str
    request_id: str | None = None


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/metrics")
def metrics():
    avg = _metrics["total_ms"] / max(_metrics["requests"], 1)
    return {**_metrics, "avg_ms": round(avg, 1), "cache_size": len(_cache)}


@app.exception_handler(Exception)
async def unhandled(request, exc):
    _metrics["errors"] += 1
    return JSONResponse(status_code=503,
                        content={"detail": f"服务暂时不可用：{type(exc).__name__}"})


def _cache_key(req: Ask) -> str:
    # request_id 优先：同一个请求重试时直接返回上次结果，避免重复计费
    return req.request_id or req.question


@app.post("/chat")
async def chat(req: Ask):
    key = _cache_key(req)
    now = time.time()
    hit = _cache.get(key)
    if hit and now - hit[0] < CACHE_TTL:
        _metrics["cache_hits"] += 1
        return {"answer": hit[1], "cached": True}

    _metrics["requests"] += 1
    t0 = time.time()
    async with _sem:
        loop = asyncio.get_running_loop()
        ans = await loop.run_in_executor(_executor, run_graph, req.question)
    _metrics["total_ms"] += (time.time() - t0) * 1000
    _cache[key] = (now, ans)
    return {"answer": ans, "cached": False}


@app.post("/chat/handwritten")
async def chat_handwritten(req: Ask):
    _metrics["requests"] += 1
    async with _sem:
        loop = asyncio.get_running_loop()
        ans = await loop.run_in_executor(_executor, run_handwritten, req.question)
    return {"answer": ans}


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
