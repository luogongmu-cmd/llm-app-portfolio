---
type: 每日任务
day: 1
duration: 45min
status: 未开始
deliverable: 公开仓库 + 一次有真实输出的 LLM API 调用
tags: [7天计划, 求职资产, Day1]
created: 2026-11-15
---

# Day 1 · 岗位反推与项目骨架

> 今天不学新技术。产出是「一个公开的、有明确规格的仓库」+ 确认 API 能跑通。
> **前置**：[[00_项目骨架与环境]] 已做完（目录树、venv、`.gitignore`、`.env` 都在）。没做就先补那 20 分钟，它不计入 45 分钟。

## 45 分钟怎么分

| 时间 | 动作 |
| --- | --- |
| 0–10 | 招聘站找 3 个「大模型应用开发 / Agent 开发」初级或 1–2 年档 JD，把硬关键词抄到本篇末尾，标出出现 ≥2 次的 |
| 10–22 | `git init` → 建公开仓库 → 推送；README 按下面模板填满 |
| 22–40 | 跑通 `smoke_test.py`（骨架见下），输出贴进打卡 |
| 40–45 | commit + 打卡 |

## README 首屏（直接改，别从空白页写）

```markdown
# 私有文档问答与工具调用 Agent

给一批私有 Markdown 文档，能问答、能拒答、能调用工具，并用一张评测表证明效果。

**在线 Demo**：（Day6 补链接）
**技术栈**：Python · LLM/Embedding API · chromadb · FastAPI · Docker

## 两个项目
1. 本项目：手写 RAG + 工具调用 + 评测（第 0 周完成）
2. 带权限边界的业务 Agent（第 3–4 周）
```

## `smoke_test.py`（复制即用，只依赖 `.env`）

```python
import os
import time

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(
    api_key=os.environ["LLM_API_KEY"],
    base_url=os.environ["LLM_BASE_URL"],
)

t0 = time.time()
resp = client.chat.completions.create(
    model=os.environ["LLM_MODEL"],
    messages=[{"role": "user", "content": "用一句话说明 RAG 是什么"}],
)
print("ANSWER :", resp.choices[0].message.content)
print("TOKENS :", resp.usage.total_tokens)
print("LATENCY:", round(time.time() - t0, 2), "s")
```

这三行输出就是 Day 8 面试题「你的 Demo 一次问答花多少钱、多少秒」的原始数据来源。

## 完成标准（全勾才算过）

- [ ] 3 个 JD 的关键词填进「JD 采样」，标出高频项
- [ ] 仓库为 public，README 含上面首屏结构，技术栈 ≤ 5 项
- [ ] `python smoke_test.py` 打印 **ANSWER / TOKENS / LATENCY 三行真实值**（贴进打卡）
- [ ] `git log --oneline` 至少 1 条 commit
- [ ] `git ls-files | grep -c "\.env$"` 输出 **0**（key 没进仓库）

## 今天最容易犯的两条（完整清单见 [[不做什么清单]]）

- ❌ 装 LangChain / LangGraph「先备着」
- ❌ 打开 Dify 搭个工作流当今天的成果（那不是新证据）

## 卡住时的最短解法

| 卡点 | 处理 |
| --- | --- |
| 没 key / 额度不通 | 换本地 Ollama：`LLM_BASE_URL=http://localhost:11434/v1`、`LLM_API_KEY=ollama`，模型填 `ollama list` 里的名字 |
| 找不到合适 JD | 用 [[目标与验收标准]] 第 4 节的能力对照表代替，继续往下做 |
| README 写不出「价值」 | 抄句式：「给 X 场景的人，输入 Y，自动得到 Z，且能验证对错」 |
| push 失败 | `git init` → 建空仓库 → `git remote add origin ...` → `git push -u origin main`；卡超 5 分钟就只留本地 commit，明天再推 |

## JD 采样（自己填，别跳过）

| JD 来源 | 硬关键词 | 出现次数 |
| --- | --- | --- |
|  |  |  |
|  |  |  |
|  |  |  |

高频项（≥2 次）：`待填`

## 关联

[[00_项目骨架与环境]] · [[Day2_手写最小RAG]] · [[目标与验收标准]] · [[不做什么清单]] · [[每日打卡模板]]
