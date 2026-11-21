# 我手写的循环和 LangGraph 差在哪

> 对应 8 周路线图第 1–2 周。结论先说：**框架没有让效果变好，它让「状态和分支」从代码里浮到图上。**
> 数据来自本地实测日志（`agent_graph.py` 的 JSON 日志），不是估算。

## 1. 两个版本各自长什么样

| | 手写版 `agent_loop.py` | LangGraph 版 `agent_graph.py` |
| --- | --- | --- |
| 控制流 | `for rnd in range(1, MAX_ROUNDS + 1)` | `StateGraph` + `add_conditional_edges` |
| 状态 | `msgs` 列表 + 局部变量 | `State` TypedDict，节点返回增量 |
| 分支 | `if not msg.tool_calls` / `except` | `route_plan` / `route_reflect` 两个路由函数 |
| 重试 | 固定 3 轮，工具错误回灌 | 证据不足才重检，`MAX_ROUNDS=2` |
| 可观测 | 自己 print / 加日志 | `GRAPH.stream(stream_mode="updates")` 直接给节点事件 |

## 2. 框架替我省掉了什么

1. **状态流转**：手写版把「第几轮、上次检索到什么、上次错在哪」散在 `msgs` 和局部变量里；LangGraph 把它们收进一个 `State`，每个节点只返回自己改的字段，条件边根据 state 决定下一步。加一个节点不用改主循环。
2. **条件分支显式化**：手写版的「证据不足就重试」藏在 `for` 循环和 `if` 里；LangGraph 写成两条边 `reflect → retrieve` / `reflect → answer`，图能直接画出来，面试时也好讲。
3. **节点级流式**：`/chat/stream` 的 SSE 直接消费 `GRAPH.stream()`，不用自己在循环里埋 `yield`。实测事件序列是 `plan → retrieve(5 hits) → reflect → answer`。
4. **（未用但值得提）checkpoint**：多轮会话恢复、断点续跑，手写要自己存 state，LangGraph 有现成机制。

## 3. 框架新增了什么成本

1. **依赖变重**：装 `langgraph` 连带 `langchain-core`、`langsmith` 等约 10 个包；镜像体积和启动时间都涨了。
2. **调试从「读代码」变成「读图 + 读 state」**：出问题要先看节点输入输出，而不是顺着一行行读。手写版反而更直观。
3. **抽象会藏细节**：超时、重试这些生产问题框架不会自动给你，还是要在 `retrieve` 节点里自己包 `ThreadPoolExecutor` + 15s 超时。

## 4. 实测数据（本地，2026-11-21）

一次「知识库里 chunk_size 默认多少」的 LangGraph 调用：

```json
{"event": "plan", "need_retrieval": true}
{"event": "retrieve", "round": 1, "hits": 5, "ms": 5356}
{"event": "reflect", "hits": 5, "rounds": 1}
{"event": "answer", "mode": "rag", "hits": 5, "tokens": 873, "ms": 4694}
```

闲聊「你好」走 `plan → answer(mode=chat)`，75 token，5.4 秒。

## 5. 结论

先手写再上框架的价值在于：**能说清每个节点为什么存在、框架替掉了哪段代码**。如果一开始就用 LangGraph，面试官问「不用框架你会怎么写」，大概率答不上来。现在两个版本都在仓库里，可以直接对照。
