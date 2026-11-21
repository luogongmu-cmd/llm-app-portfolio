"""FastAPI 服务：并发限制、超时/重试、缓存、幂等（request_id）与 /metrics。"""
import asyncio
import json
import time
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
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


INDEX_HTML = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>私有文档问答与工具调用 Agent</title>
<style>
  :root { --bg:#f8fafc; --card:#fff; --line:#e2e8f0; --text:#0f172a; --muted:#64748b; --blue:#2563eb; }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--bg); color:var(--text); font-family: system-ui, -apple-system, "Segoe UI", "Microsoft YaHei", sans-serif; }
  main { max-width: 780px; margin: 48px auto; padding: 0 16px; }
  h1 { font-size: 24px; margin: 0 0 6px; }
  .sub { color: var(--muted); font-size: 14px; margin: 0 0 24px; line-height: 1.6; }
  .card { background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: 18px; }
  .row { display: flex; gap: 8px; flex-wrap: wrap; }
  input, button { font: inherit; padding: 10px 12px; border-radius: 8px; border: 1px solid var(--line); }
  input { flex: 1 1 280px; min-width: 0; }
  button { background: var(--blue); color: #fff; border-color: var(--blue); cursor: pointer; }
  button:disabled { opacity: .6; cursor: wait; }
  .examples { margin-top: 10px; display: flex; gap: 8px; flex-wrap: wrap; }
  .examples button { background: #eff6ff; color: #1d4ed8; border-color: #bfdbfe; font-size: 13px; padding: 6px 10px; }
  #answer { margin-top: 16px; white-space: pre-wrap; line-height: 1.75; min-height: 90px; }
  .hint { color: var(--muted); font-size: 13px; }
  .err { color: #b91c1c; }
</style>
</head>
<body>
<main>
  <h1>私有文档问答与工具调用 Agent</h1>
  <p class="sub">基于 LangGraph 的 plan → retrieve → reflect → answer 链路；资料里没有答案时直接拒答，不编造。</p>
  <div class="card">
    <div class="row">
      <input id="q" placeholder="例如：知识库里 chunk_size 默认多少" autocomplete="off" />
      <button id="send">发送</button>
    </div>
    <div class="examples">
      <button data-q="知识库里 chunk_size 默认多少">chunk_size</button>
      <button data-q="Day4 建议把 overlap 从多少改到多少">overlap 实验</button>
      <button data-q="这个项目的月活用户是多少">无答案问题</button>
    </div>
    <div id="answer" class="hint">等待提问…</div>
  </div>
</main>
<script>
const $ = (id) => document.getElementById(id);
async function ask() {
  const q = $('q').value.trim();
  if (!q) return;
  $('send').disabled = true;
  $('answer').className = 'hint';
  $('answer').textContent = '检索中…';
  try {
    const r = await fetch('/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({question: q})
    });
    const j = await r.json();
    if (!r.ok) { $('answer').className = 'err'; $('answer').textContent = j.detail || '请求失败'; return; }
    $('answer').className = '';
    $('answer').textContent = j.answer;
  } catch (e) {
    $('answer').className = 'err';
    $('answer').textContent = '网络错误：' + e.message;
  } finally {
    $('send').disabled = false;
  }
}
$('send').onclick = ask;
$('q').addEventListener('keydown', e => { if (e.key === 'Enter') ask(); });
document.querySelectorAll('.examples button').forEach(b => b.onclick = () => { $('q').value = b.dataset.q; ask(); });
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def index():
    return INDEX_HTML


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
