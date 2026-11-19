---
type: 每日任务
day: 4
duration: 45min
status: 未开始
deliverable: 同一评测集上的「改动前 vs 改动后」对比表
tags: [7天计划, 优化归因, Day4]
created: 2026-11-15
---

# Day 4 · 只做一个改动，跑同一套评测

> 今天练的不是「把效果调好」，是**归因能力**：能不能说清「哪个改动解决了哪个 case，为什么」。
> 这是简历上唯一能被追问两轮还不虚的东西。
> 三个候选改动下面都给了代码，**选一个，只改一处**。

## 45 分钟怎么分

| 时间 | 动作 |
| --- | --- |
| 0–10 | 从 [[Day3_建评测集]] 的失败案例里选 1 个，写下假设：「做 A 会解决 case #X，因为……」，**先写再改代码** |
| 10–30 | 只改一处（从下面三个里挑），必要时重建索引 |
| 30–40 | 把 `eval.py` 的输出文件改成 `after.json`，重跑同样 20 条 |
| 40–45 | README 并排放前后两张表 + 一句归因结论，commit |

## 三个候选改动（挑一个，都有具体做法）

### ① 调整 overlap：50 → 100（最简单，专治跨段被切断）

改 `ingest.py` 的 `OVERLAP = 100`，**然后必须重建索引**，否则指标不会变：

```bash
rm -rf .chroma && python ingest.py
```

### ② 简单重排：先多取，再按中文 2-gram 重合度重排取前 3

在 `query.py` 加一个函数，并在 `answer()` 里用它替换 `search()` 的直接结果：

```python
import re


def grams(s: str, n: int = 2) -> set:
    s = re.sub(r"\s+", "", s)
    return {s[i:i + n] for i in range(len(s) - n + 1)}


def rerank(question: str, hits: list[dict], top: int = 3) -> list[dict]:
    q = grams(question)
    return sorted(hits, key=lambda h: len(q & grams(h["text"])), reverse=True)[:top]


# answer() 里改成：
#   hits = rerank(question, search(question, k=8))
```

### ③ 来源过滤：只保留与问题最相关文档的片段

先粗检索 8 条，再按 `source` 去重，每个文档只留最靠前的一条：

```python
def dedup_by_source(hits: list[dict], top: int = 3) -> list[dict]:
    seen, out = set(), []
    for h in hits:
        if h["source"] in seen:
            continue
        seen.add(h["source"])
        out.append(h)
        if len(out) == top:
            break
    return out


# answer() 里改成：
#   hits = dedup_by_source(search(question, k=8))
```

> 这就是 Day2 坚持存 `source` 元数据的原因。没存的话，改动 ③ 根本做不了。

## 完成标准（全勾才算过）

- [ ] 假设写在结果前面，且指向具体 case 编号（如 `q07`）
- [ ] `git diff` 能证明只改了一处（或一组同性质参数）
- [ ] 前后两张表并排：`runs/before.json` 与 `runs/after.json`，条数相同
- [ ] 写了一句归因结论：涨了说清为什么涨，**跌了也照实写为什么跌**（跌了同样算完成）
- [ ] 有 commit

## 今天最容易犯的两条（完整清单见 [[不做什么清单]]）

- ❌ 同时改 prompt、切片、模型三处 → 无法归因，等于白做
- ❌ 换更贵/更大的模型当成「优化」（那是加钱，不是工程能力）

## 卡住时的最短解法

| 卡点 | 处理 |
| --- | --- |
| 想不出改什么 | 选 ①，`OVERLAP = 100` + `rm -rf .chroma && python ingest.py` |
| 指标完全没变 | 完成。写「假设不成立，因为……」，这比刷漂亮数字更有说服力 |
| 改了但指标不变 | 90% 是**没重建索引**，先确认 `.chroma` 已删、`ingest.py` 重跑过 |
| 30 分钟没改完 | 回退到能跑的最小版本，今天仍要交一张对比表 |

## 关联

[[Day3_建评测集]] · [[Day2_手写最小RAG]] · [[Day5_工具调用与异常处理]] · [[简历项目描述模板]] · [[交付自检脚本]]
