---
type: 每日任务
day: 5
duration: 45min
status: 未开始
deliverable: 工具调用成功对话 + 3 类失败不崩溃的演示记录
tags: [7天计划, FunctionCalling, 异常处理, Day5, 关键差异化]
created: 2026-11-15
---

# Day 5 · 手写工具分发循环 + 故意制造 3 种失败

> 2026 年 JD 最常被吐槽的一句是「只会复制 Demo，对异常、状态流转、生产问题缺少处理经验」。
> 今天专门打这一枪：**不用任何 Agent 框架**，手写循环，然后亲手把它弄坏三次。

## 45 分钟怎么分

| 时间 | 动作 |
| --- | --- |
| 0–10 | 写 `tools.py`：2 个工具 schema + `dispatch()`（骨架见下） |
| 10–30 | 写 `agent_loop.py`：tool_calls → 执行 → 回灌 → 出答案，**最多 3 轮** |
| 30–42 | 用 `FAULT_MODE` 跑 3 类失败，各截一段记录 |
| 42–45 | 4 段对话（1 成功 + 3 失败）贴进 README，commit |

## `tools.py`

```python
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
        return search(q)

    if name == "calculator":
        expr = args.get("expr", "")
        if not re.fullmatch(r"[0-9+\-*/(). ]+", expr):
            raise ValueError("表达式只能包含数字和 + - * / ( )")
        return eval(expr, {"__builtins__": {}})

    raise ValueError(f"未知工具：{name}")
```

## `agent_loop.py`

```python
import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from tools import TOOLS, dispatch

load_dotenv()
client = OpenAI(api_key=os.environ["LLM_API_KEY"], base_url=os.environ["LLM_BASE_URL"])
MAX_ROUNDS = 3


def run(question: str) -> str:
    msgs = [
        {"role": "system", "content": "回答事实性问题前必须先调用 search_kb 检索，不要凭记忆作答。"},
        {"role": "user", "content": question},
    ]
    for rnd in range(1, MAX_ROUNDS + 1):
        resp = client.chat.completions.create(
            model=os.environ["LLM_MODEL"], messages=msgs, tools=TOOLS
        )
        msg = resp.choices[0].message

        if not msg.tool_calls:                      # 模型认为可以直接回答
            return msg.content or "（模型未给出答案）"

        msgs.append(msg)
        for call in msg.tool_calls:
            try:
                args = json.loads(call.function.arguments or "{}")
                result = dispatch(call.function.name, args)
            except Exception as exc:
                # 关键：把「可行动的错误原因」回灌给模型，而不是抛栈或返回 null
                result = f"TOOL_ERROR: {type(exc).__name__}: {exc}。请修正参数，或说明无法完成。"
            msgs.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(result, ensure_ascii=False),
            })

    return f"已达到工具调用上限（{MAX_ROUNDS} 轮），无法继续。请把问题拆小或补充信息。"


if __name__ == "__main__":
    print(run(input("问题：")))
```

## 制造 3 种失败（照抄命令，Git Bash 直接可用）

```bash
# ① 模型不调工具：问纯闲聊，观察它直接回答、循环正常退出
python agent_loop.py            # 输入：你好，你是谁

# ② 参数缺失：dispatch 收到空 dict，必须抛出可行动错误
FAULT_MODE=missing python agent_loop.py    # 输入：知识库里 chunk_size 默认多少

# ③ 工具内部异常：模拟向量库挂了
FAULT_MODE=raise python agent_loop.py      # 同一问题
```

三次都要看到：**没有 traceback 甩给用户、循环没卡死、回复里说明了发生了什么**。

## 完成标准（全勾才算过）

- [ ] 有一条「不调工具就答不出来」的问题，走完 工具调用 → 回灌 → 正确答案 全流程
- [ ] 3 类失败各有一段真实记录，**没有 traceback 直接甩给用户**
- [ ] `MAX_ROUNDS` 上限生效，超限返回明确说明而非静默空结果
- [ ] 工具失败时回灌给模型的内容包含可行动原因（不是只回 `null`）
- [ ] 代码里没有 import LangGraph / Agent 框架
- [ ] 有 commit

## 今天最容易犯的两条（完整清单见 [[不做什么清单]]）

- ❌ 直接上 LangGraph / Agent 框架（[[8周路线图]] 第 1–2 周才做）
- ❌ 用 `except: pass` 吞掉异常、只跑 happy path 就收工

## 卡住时的最短解法

| 卡点 | 处理 |
| --- | --- |
| 模型死活不调工具 | system prompt 再加一句「不确定时也必须先检索」；仍不调就把它记成第 ① 类失败 |
| `msgs.append(msg)` 报类型错 | 用 `msgs.append(msg.model_dump())` 转成 dict |
| 参数解析繁琐 | 保持 `if name == ...` 分发，不做通用反射 |
| 40 分钟只做完循环 | 保「成功对话 + 轮数上限」，3 类失败至少留 1 段，其余次日补 |

> 这 4 段对话记录，面试时比任何「熟悉 Agent 开发」的形容词都管用。

## 关联

[[Day2_手写最小RAG]] · [[Day4_单次可归因优化]] · [[Day6_服务化与公网可访问]] · [[面试自检题库]] · [[每日打卡模板]]
