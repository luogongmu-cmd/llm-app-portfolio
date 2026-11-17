# 私有文档问答与工具调用 Agent

给一批私有 Markdown 文档，能问答、能拒答、能调用工具，并用一张评测表证明效果。

> 当前进度：Day 2 / 7 —— 最小 RAG 链路已跑通（切片 → embedding → 检索 → 生成 → 打印来源）

## 两个项目

1. 本项目：手写 RAG + 工具调用 + 评测（第 0 周完成）
2. 带权限边界的业务 Agent（第 3–4 周）

## 技术栈

Python 3.10+ · OpenAI 兼容 API（LLM + Embedding）· Chroma · FastAPI（Day 6）· Docker（Day 6）

## 快速开始

```bash
# 1. 环境
python -m venv .venv
source .venv/Scripts/activate        # Git Bash；PowerShell 用 .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. 配置（填 4 个变量：LLM_API_KEY / LLM_BASE_URL / LLM_MODEL / EMBED_MODEL）
cp .env.example .env

# 3. 建索引
python ingest.py

# 4. 提问（交互式，会打印 3 个命中片段 + 来源 + distance + 答案）
python query.py

# 5. 连通性自检（打印 ANSWER / TOKENS / LATENCY）
python smoke_test.py
```

## 语料

`data/corpus/` 不进版本库（见 `.gitignore`），请自备 Markdown 文档放进去，例如：

```bash
mkdir -p data/corpus
cp /path/to/your/notes/*.md data/corpus/
```

本项目开发时用自己写的知识库笔记作为语料（11 篇），好处是答案已知、便于出评测题。

## 目录结构

```text
.
├── ingest.py        # 切片 + embedding + 入 Chroma
├── query.py         # 检索 + 拼 prompt + 生成（search() 供 Day5 复用）
├── smoke_test.py    # 最小连通性自检
├── check.py         # 交付自检（待补）
├── tools.py         # 工具调用（Day5）
├── agent_loop.py    # 手写分发循环（Day5）
├── app.py           # FastAPI 服务（Day6）
├── eval/            # 评测集与评测脚本（Day3）
├── data/corpus/     # 语料（不提交）
└── .chroma/         # 本地向量库（不提交）
```

## 评测

待 Day 3 补充：20 条评测集 + Recall@K / MRR / 拒答正确率，以及与基线的对比。

## 已知限制

- 固定窗口切分（500 / 50），片段不带章节上下文，跨章节问题命中率有限
- 纯向量检索，对型号、编号等精确串不敏感（Day 4 计划加 BM25 + 重排）
- 单机 Chroma，未做并发与权限
- 仅支持文字版 Markdown

## License

MIT
