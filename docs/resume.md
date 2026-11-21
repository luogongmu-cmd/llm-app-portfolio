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
- 在手写版之外用 LangGraph `StateGraph` 重写为 `plan → retrieve → reflect → answer` 四节点（条件边 + 15s 检索超时），补 SSE 流式与结构化日志；GitHub Actions 提交即跑自检。

## 2. 企业知识库权限 Agent

**技术栈**：Python · Chroma · FastAPI · Docker
**GitHub**：https://github.com/luogongmu-cmd/kb-acl-agent
**Demo**：https://kb-acl-agent.onrender.com

- 针对「同一知识库不同部门可见范围不同」的约束，把 ACL 放在检索层：每个 chunk 写入 `acl_<dept>` 字段，查询时按角色 `where` 过滤，越权文档不进上下文。
- 自建 12 条权限评测（6 权限内 / 3 越权 / 3 公共），权限内命中率 **1.00**、越权拒答率 **1.00**、权限违规 **0**。
- 加成本控制与降级：每角色 20 次/分钟限流、60 秒答案缓存、上下文 5 段 × 400 字；检索异常返回 503 可读原因。
- 复盘记录一次真实 bug：`public` 字段误写到 HR 文档，导致 guest 能看到薪酬内容，改为「文档只写本部门字段 + 查询 `public OR 本部门`」。
