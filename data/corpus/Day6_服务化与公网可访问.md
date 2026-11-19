---
type: 每日任务
day: 6
duration: 45min
status: 未开始
deliverable: 面试官点得开的 Demo 链接 + 架构图 + 启动文档
tags: [7天计划, FastAPI, 部署, Day6]
created: 2026-11-15
---

# Day 6 · 包一层服务，让陌生人能打开

> 前 5 天的代码只在你的终端里跑过，对面试官等于不存在。今天让它变成一个链接。
> **只需要「能访问」**，不需要好看、可伸缩、有登录。

## 45 分钟怎么分

| 时间 | 动作 |
| --- | --- |
| 0–15 | 写 `app.py`（骨架见下），本机 `uvicorn` 跑通 `POST /chat` |
| 15–25 | `Dockerfile` + `.env.example`；确认 key 不在仓库 |
| 25–38 | 部署到能公网访问的地方，拿到 URL 后用 `curl` 验证 |
| 38–45 | README 加架构图 + 截图 + 「已知限制」，commit |

## `app.py`

```python
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
```

本机验证：

```bash
uvicorn app:app --reload --port 8000
curl -s -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"chunk_size 和 overlap 默认多少"}'
```

## `Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

**一个必须知道的坑**：容器里没有 `.chroma/` 就没有索引。
本地构建前先确认 `python ingest.py` 跑过；`.gitignore` 里已忽略 `.chroma/`（不进 git），但 `COPY . .` 会把它带进镜像。
这正好写成 README 的一条已知限制：「索引随镜像打包，语料更新需重建镜像」。

## 部署：三类，按「15 分钟内能出链接」挑

| 方式 | 适合 | 注意 |
| --- | --- | --- |
| 内网穿透（本机 `uvicorn` + 穿透工具） | **最快**，无需构建 | 本机关机就失效，README 注明 |
| 免费容器托管（认 Dockerfile） | 有 Dockerfile 即可 | 首次构建可能超 15 分钟，超时就换穿透 |
| 已有云服务器（`docker run`） | 你手上有机器 | 注意端口与安全组 |

判断标准只有一条：**别人能不能打开并问出一个正确答案**。

## 完成标准（全勾才算过）

- [ ] 用**无痕窗口或另一台设备**打开链接，问一个文档里有答案的问题，得到正确答案
- [ ] README 有架构图（Mermaid 三五个框）、启动命令、环境变量说明
- [ ] README 写了至少 2 条已知限制（如「仅单机无并发限流」「索引随镜像打包」）
- [ ] 仓库中没有任何 API key，`.env` 未被跟踪
- [ ] 有 commit

## 今天最容易犯的两条（完整清单见 [[不做什么清单]]）

- ❌ K8s / 负载均衡 / 监控大盘 / CI 流水线（第 1–2 周再说）
- ❌ 域名、备案、HTTPS、登录系统、前端美化

## 卡住时的最短解法

| 卡点 | 处理 |
| --- | --- |
| 部署平台注册/构建超 15 分钟 | **立刻换内网穿透**，先拿到链接 |
| Docker 构建慢 | 先裸跑 `uvicorn`，Dockerfile 留着不构建，链接优先 |
| 容器里检索为空 | `.chroma/` 没进镜像，本地先 `python ingest.py` 再 build |
| 公网被限 | 录 60 秒终端演示 + 截图放 README，打卡里如实标「公网未通」 |

> 部署不是今天的重点，**别让它吃掉整个 45 分钟**。拿到链接就停手。

## 关联

[[Day5_工具调用与异常处理]] · [[Day7_简历与面试弹药]] · [[作品集项目规格]] · [[8周路线图]] · [[每日打卡模板]]
