# 简历项目描述（2 条）

> 数字出处：`eval/runs/before.json`、`eval/runs/after.json`、README 评测表、Render 启动日志。
> 规则：每条至少 1 个可验证数字 + 1 个技术取舍；不写「熟悉 / 精通 / 了解」。

## 1. 私有文档问答与工具调用 Agent

**技术栈**：Python · Chroma · FastAPI · Docker
**GitHub**：https://github.com/luogongmu-cmd/llm-app-portfolio
**Demo**：https://llm-app-portfolio.onrender.com

- 针对通用大模型在私有语料上编造参数的问题，手写「切片 → 向量检索 → 上下文拼装 → 拒答」链路，答案强制附带来源片段，无依据时返回「资料中没有」。
- 自建 20 条评测集（10 可答 / 5 应拒答 / 5 跨段综合），用检索命中率、拒答正确率、要点覆盖率三项指标量化，首版为 **0.90 / 1.00 / 0.80**；仅把 `overlap` 从 50 改到 100 做单变量实验，命中率反而降到 **0.80**，定位到「同文档重复片段挤占 top3」并回退。
- 手写 Function Calling 分发循环（≤3 轮），用 `FAULT_MODE` 复现模型不调工具、参数缺失、工具抛异常三类失败，均降级为可读说明而非抛栈；超轮时回带最后一次工具错误。
- FastAPI + Docker 服务化，容器启动自动建索引（**71 片段**），Render 公网可访问；README 含架构图、评测对比表与 5 条已知限制。

## 2. LangGraph 多轮 Agent（进行中，第 1–2 周）

**技术栈**：Python · LangGraph · FastAPI · Docker

- 用 `StateGraph` 重写 Day5 的手写分发循环，节点拆为 `plan → retrieve → reflect → answer`，用条件边实现「证据不足则改写重检」，替代原来的固定 3 轮 `for` 循环。
- 补多轮状态与超时重试：状态在 graph 内流转，工具调用加超时与一次重试，失败原因写入 state 供下一节点使用。
- 加结构化日志埋点（检索来源、token、耗时、失败原因）与 SSE 流式接口，把「一次问答多少 token / 多少秒」变成可查询的数据。
- 提交即跑 `check.py` 与评测脚本的 CI；复盘文章《我手写的循环和 LangGraph 差在哪》说明框架替我省掉了什么、又新增了什么。
