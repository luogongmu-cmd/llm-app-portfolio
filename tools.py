import os
import re

from query import search  # Day2 的实现，签名别改

FAULT = os.getenv("FAULT_MODE", "")   # "" | "missing" | "raise"

TOOLS = [
    {"type": "function", "function": {
        "name": "search_kb",
        "description": "在私有知识库中检索资料。回答事实性问题前必须先调用。",
        "parameters": {"type": "object",
                       "properties": {"query": {"type": "string", "description": "检索关键词"}},
                       "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "calculator",
        "description": "计算只含数字与 + - * / ( ) 的算术表达式",
        "parameters": {"type": "object",
                       "properties": {"expr": {"type": "string"}},
                       "required": ["expr"]}}},
]


def dispatch(name: str, args: dict):
    if FAULT == "raise":                      # 演示工具内部异常
        raise RuntimeError("向量库连接超时（FAULT_MODE=raise）")
    if FAULT == "missing":                    # 演示参数缺失
        args = {}

    if name == "search_kb":
        q = args.get("query")
        if not q:
            raise ValueError("缺少 query 参数，请提供检索关键词")
        hits = search(q)
        # 只回灌正文与来源：distance 是给调试看的，传给模型会干扰判断
        return [{"text": h["text"][:400], "source": h["source"]} for h in hits]

    if name == "calculator":
        expr = args.get("expr", "")
        if not re.fullmatch(r"[0-9+\-*/(). ]+", expr):
            raise ValueError("表达式只能包含数字和 + - * / ( )")
        return eval(expr, {"__builtins__": {}})

    raise ValueError(f"未知工具：{name}")