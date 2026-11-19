---
type: 每日任务
day: 2
duration: 45min
status: 未开始
deliverable: 不用任何框架、能打印命中片段与来源的命令行 RAG
tags: [7天计划, RAG, Day2]
created: 2026-11-15
---

# Day 2 · 手写最小 RAG（禁用框架）

> 把你在 Dify 里拖过的「知识检索」节点，用 Python 手写一遍。
> 今天**不追求效果好**，只追求链路通、能看见中间结果。
> 下面的骨架是「填空级」的：改 `.env` 和 3 个常量就能跑。别从空白文件开始写。

## 45 分钟怎么分

| 时间 | 动作 |
| --- | --- |
| 0–5 | 确认 `data/corpus/` 有 11 篇左右 md，`python -c "import chromadb"` 不报错 |
| 5–20 | 写 `ingest.py`（骨架见下）：切片 → embedding → 入本地库 |
| 20–40 | 写 `query.py`（骨架见下）：检索 top3 → 拼 prompt → 生成 → **打印来源、片段、距离、答案** |
| 40–45 | commit |

## `ingest.py`（关键在 `metadatas`，Day4 要用）

```python
import glob
import os

import chromadb
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
CHUNK, OVERLAP = 500, 50          # Day4 会改这里，别今天调
COLLECTION = "kb"

client = OpenAI(api_key=os.environ["LLM_API_KEY"], base_url=os.environ["LLM_BASE_URL"])
col = chromadb.PersistentClient(path=".chroma").get_or_create_collection(COLLECTION)


def chunk(text, size=CHUNK, overlap=OVERLAP):
    out, i = [], 0
    while i < len(text):
        out.append(text[i:i + size])
        i += size - overlap
    return out


for path in sorted(glob.glob("data/corpus/*.md")):
    name = os.path.basename(path)
    text = open(path, encoding="utf-8").read()
    for idx, piece in enumerate(chunk(text)):
        emb = client.embeddings.create(
            model=os.environ["EMBED_MODEL"], input=piece
        ).data[0].embedding
        col.add(
            ids=[f"{name}-{idx}"],
            documents=[piece],
            embeddings=[emb],
            # source 必须存：Day3 算命中率、Day4 做过滤都靠它
            metadatas=[{"source": name, "idx": idx}],
        )

print("indexed chunks:", col.count())
```

## `query.py`（`search()` 会被 Day5 直接复用，签名别改）

```python
import os

import chromadb
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.environ["LLM_API_KEY"], base_url=os.environ["LLM_BASE_URL"])
col = chromadb.PersistentClient(path=".chroma").get_or_create_collection("kb")


def search(question: str, k: int = 3) -> list[dict]:
    """返回 [{'text','source','distance'}]，distance 越小越相似。"""
    emb = client.embeddings.create(
        model=os.environ["EMBED_MODEL"], input=question
    ).data[0].embedding
    r = col.query(query_embeddings=[emb], n_results=k)
    return [
        {"text": d, "source": m["source"], "distance": round(dist, 4)}
        for d, m, dist in zip(
            r["documents"][0], r["metadatas"][0], r["distances"][0]
        )
    ]


def answer(question: str, k: int = 3) -> str:
    hits = search(question, k)
    ctx = "\n\n".join(f"[{h['source']}] {h['text']}" for h in hits)
    prompt = (
        "只根据下面的资料回答。资料里没有答案时，直接回答「资料中没有」。\n\n"
        f"{ctx}\n\n问题：{question}"
    )
    resp = client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content


if __name__ == "__main__":
    q = input("问题：")
    for h in search(q):
        print(f"\n--- {h['source']} | distance={h['distance']}")
        print(h["text"][:200].replace("\n", " "))
    print("\n=== 答案 ===\n", answer(q))
```

## 完成标准（全勾才算过）

- [ ] 命令行问一个文档里**明确写了**答案的问题，返回正确答案
- [ ] 输出里能看到 **3 个命中片段 + 来源文件名 + distance**（不是只输出答案）
- [ ] `ingest.py` 的 `metadatas` 里有 `source` 字段（Day3/Day4 依赖它）
- [ ] 代码里没有 import 任何 RAG / Agent 框架，也没调用 Dify
- [ ] 能用一句话解释 `chunk_size=500 / overlap=50`（说不出就写「先设默认值，待评测验证」，也算过）
- [ ] 有 commit

## 今天最容易犯的两条（完整清单见 [[不做什么清单]]）

- ❌ 反复调 prompt 直到「效果好」——效果交给 [[Day3_建评测集]] 和 [[Day4_单次可归因优化]]
- ❌ 换向量库、研究 HNSW 参数、加 Web UI / 多轮 / 记忆

## 卡住时的最短解法

| 卡点 | 处理 |
| --- | --- |
| embedding 接口慢或报错 | 先用 `hash(piece)` 占位只为验证链路；**进 Day3 前必须换成真 embedding**，否则检索指标毫无意义 |
| `col.add` 报 id 重复 | 先 `col.delete(where={"source": name})` 再写，或换 collection 名 |
| 检索不准 | **不要调**，记成失败案例，正好是 Day3 的输入 |
| 45 分钟到点没跑通 | 只保留「检索 + 打印片段」，`answer()` 先返回拼接文本占位，仍算过 |

> 判断标准始终是「有没有留下可验证证据」，不是「功能全不全」。

## 关联

[[00_项目骨架与环境]] · [[Day1_岗位反推与项目骨架]] · [[Day3_建评测集]] · [[Day4_单次可归因优化]] · [[每日打卡模板]]
