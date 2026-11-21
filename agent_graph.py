"""LangGraph 版 Agent：plan → retrieve → reflect → answer。

与手写版 `agent_loop.py` 的分工：
- `agent_loop.py` 保留为「手写循环」对照，证明说得清框架替我们做了什么；
- 本文件用 StateGraph 表达同样的链路，但把状态、条件分支、重试显式化。

第 1–2 周新增：条件边（证据不足则改写重检）、超时重试、结构化日志。
"""
import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from typing import Literal, TypedDict

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph
from openai import OpenAI

from tools import dispatch

load_dotenv()
client = OpenAI(api_key=os.environ["LLM_API_KEY"], base_url=os.environ["LLM_BASE_URL"])
MODEL = os.environ["LLM_MODEL"]
MAX_ROUNDS = 2
SEARCH_TIMEOUT = 15

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("agent_graph")
_pool = ThreadPoolExecutor(max_workers=2)


class State(TypedDict, total=False):
    question: str
    query: str
    hits: list
    rounds: int
    need_retrieval: bool
    answer: str
    error: str | None


def _log(event: str, **fields):
    logger.info(json.dumps({"event": event, **fields}, ensure_ascii=False))


def _search_with_timeout(query: str, timeout: int = SEARCH_TIMEOUT) -> list:
    future = _pool.submit(dispatch, "search_kb", {"query": query})
    try:
        return future.result(timeout=timeout)
    except FutureTimeout as exc:
        raise TimeoutError(f"检索超时（>{timeout}s）") from exc


def plan(state: State) -> State:
    q = state["question"]
    need = any(k in q for k in ("多少", "几", "什么", "怎么", "为什么", "哪", "是否", "区别", "介绍"))
    _log("plan", question=q, need_retrieval=need)
    return {"query": q, "rounds": 0, "need_retrieval": need}


def route_plan(state: State) -> Literal["retrieve", "answer"]:
    return "retrieve" if state.get("need_retrieval") else "answer"


def retrieve(state: State) -> State:
    rounds = state.get("rounds", 0)
    query = state["query"] if rounds == 0 else f"{state['query']} 文档 说明"
    t0 = time.time()
    try:
        hits = _search_with_timeout(query)
        _log("retrieve", round=rounds + 1, query=query, hits=len(hits),
             ms=round((time.time() - t0) * 1000))
        return {"hits": hits, "rounds": rounds + 1, "error": None}
    except Exception as exc:
        _log("retrieve_error", round=rounds + 1, error=f"{type(exc).__name__}: {exc}")
        return {"hits": [], "rounds": rounds + 1, "error": f"{type(exc).__name__}: {exc}"}


def reflect(state: State) -> State:
    hits = [h for h in state.get("hits", []) if h.get("text", "").strip()]
    _log("reflect", hits=len(hits), rounds=state.get("rounds", 0))
    return {"hits": hits}


def route_reflect(state: State) -> Literal["retrieve", "answer"]:
    if state.get("hits") or state.get("rounds", 0) >= MAX_ROUNDS:
        return "answer"
    return "retrieve"


def answer(state: State) -> State:
    t0 = time.time()
    if not state.get("need_retrieval"):
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": state["question"]}],
            temperature=0,
        )
        ans = resp.choices[0].message.content or ""
        _log("answer", mode="chat", tokens=resp.usage.total_tokens if resp.usage else None,
             ms=round((time.time() - t0) * 1000))
        return {"answer": ans}

    hits = state.get("hits", [])[:5]
    ctx = "\n\n".join(f"[{h['source']}] {h['text']}" for h in hits) or "（无检索结果）"
    prompt = (
        "只根据下面的资料回答，资料中的正文和表格条目都算有效依据。\n"
        "只有当资料里完全没有相关内容时，才回答「资料中没有」；\n"
        "若资料中有相关条目，即使表述简略也要据此作答。\n\n"
        f"{ctx}\n\n问题：{state['question']}"
    )
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    ans = resp.choices[0].message.content or ""
    _log("answer", mode="rag", hits=len(hits),
         tokens=resp.usage.total_tokens if resp.usage else None,
         ms=round((time.time() - t0) * 1000))
    return {"answer": ans}


def build_graph():
    g = StateGraph(State)
    g.add_node("plan", plan)
    g.add_node("retrieve", retrieve)
    g.add_node("reflect", reflect)
    g.add_node("answer", answer)
    g.add_edge(START, "plan")
    g.add_conditional_edges("plan", route_plan, {"retrieve": "retrieve", "answer": "answer"})
    g.add_edge("retrieve", "reflect")
    g.add_conditional_edges("reflect", route_reflect, {"retrieve": "retrieve", "answer": "answer"})
    g.add_edge("answer", END)
    return g.compile()


GRAPH = build_graph()


def run(question: str) -> str:
    out = GRAPH.invoke({"question": question, "rounds": 0})
    return out.get("answer", "")


if __name__ == "__main__":
    print(run(input("问题：")))
