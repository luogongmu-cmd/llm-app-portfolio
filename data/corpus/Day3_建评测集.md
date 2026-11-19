---
type: 每日任务
day: 3
duration: 45min
status: 未开始
deliverable: 20 条评测集 + 首版指标表 + 2 个失败案例归因
tags: [7天计划, 评测, Day3, 关键差异化]
created: 2026-11-15
---

# Day 3 · 建评测集（7 天里最值钱的一天）

> 「只会跑 Demo」和「工程师」的分界线就在今天。
> 面试官不在乎你的 Demo 能不能答对一道题，在乎你**怎么知道它答对了、错在哪**。
> 出题别从零想：直接改下面 3 条样例，改到 20 条。
> **开工第一件事**：如果 Day2 用了 `hash` 占位向量，先换成真 embedding 并重建索引（`rm -rf .chroma && python ingest.py`），否则今天的指标全是噪音。

## 45 分钟怎么分

| 时间 | 动作 |
| --- | --- |
| 0–15 | 写 `eval/cases.jsonl`：20 条，按 10 / 5 / 5 配比（模板见下） |
| 15–35 | 写 `eval/eval.py`（骨架见下），跑出 `runs/before.json` |
| 35–45 | 结果表写进 README，挑 2 个失败案例写归因，commit |

## `cases.jsonl` 字段（一行一个 JSON，不要数组）

| 字段 | 含义 | 示例 |
| --- | --- | --- |
| `id` | 唯一编号，失败案例要用它指认 | `q03` |
| `type` | `answerable` / `no_answer` / `multi_chunk` | `answerable` |
| `question` | 自然语言问题 | `chunk_size 和 overlap 默认设成多少？` |
| `expect` | 答案里**必须出现**的关键词列表 | `["500", "50"]` |
| `source` | 应命中的文档名；`no_answer` 填 `null` | `Day2_手写最小RAG.md` |

三条样例（照这个格式写满 20 条）：

```jsonl
{"id":"q01","type":"answerable","question":"chunk_size 和 overlap 默认设成多少？","expect":["500","50"],"source":"Day2_手写最小RAG.md"}
{"id":"q11","type":"no_answer","question":"这个项目的月活用户是多少？","expect":["资料中没有"],"source":null}
{"id":"q16","type":"multi_chunk","question":"为什么先手写循环再上 LangGraph？","expect":["说得清","框架"],"source":"8周路线图.md"}
```

**20 条固定配比**（别自己发挥）：
- 10 条 `answerable`：文档里能直接找到答案
- 5 条 `no_answer`：文档里**没有**答案，正确行为是拒答
- 5 条 `multi_chunk`：需要跨 2 个以上段落综合

## `eval/eval.py`（能直接跑；每一行都要能解释）

```python
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from query import answer, search  # noqa: E402  Day2 的实现

rows = [json.loads(x) for x in
        Path("eval/cases.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]

hit = refuse_ok = covered = 0
detail = []
for r in rows:
    hits = search(r["question"])
    ans = answer(r["question"])
    got_source = r["source"] is None or any(h["source"] == r["source"] for h in hits)
    has_expect = all(k in ans for k in r["expect"])

    if r["type"] == "answerable":
        hit += got_source
        covered += has_expect
    elif r["type"] == "multi_chunk":
        covered += has_expect
    else:  # no_answer
        refuse_ok += any(k in ans for k in ("资料中没有", "不知道", "无法回答"))

    detail.append({"id": r["id"], "type": r["type"], "source_hit": got_source,
                   "expect_ok": has_expect, "answer": ans[:120]})

n_ans = sum(r["type"] == "answerable" for r in rows)
n_multi = sum(r["type"] == "multi_chunk" for r in rows)
n_no = sum(r["type"] == "no_answer" for r in rows)

summary = {
    "cases": len(rows),
    "retrieval_hit_rate": round(hit / max(n_ans, 1), 3),
    "refuse_correct_rate": round(refuse_ok / max(n_no, 1), 3),
    "expect_coverage": round(covered / max(n_ans + n_multi, 1), 3),
    "detail": detail,
}
Path("eval/runs").mkdir(parents=True, exist_ok=True)
out = Path("eval/runs/before.json")   # Day4 改成 after.json 再跑一次
out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({k: v for k, v in summary.items() if k != "detail"},
                 ensure_ascii=False, indent=2))
```

## 完成标准（全勾才算过）

- [ ] `python eval/eval.py` 一条命令跑完，打印三项指标
- [ ] `eval/runs/before.json` 已生成，含 20 条明细
- [ ] README 有一张表：三指标 + 样本数 20 + 运行日期
- [ ] 20 条里确实有 5 条 `no_answer`、5 条 `multi_chunk`（**不许全出容易的题**）
- [ ] 明确写出 2 个失败案例，各有一句归因（如「overlap 太小，跨段落问题被切断」）
- [ ] 有 commit

## 今天最容易犯的两条（完整清单见 [[不做什么清单]]）

- ❌ 让大模型给自己打分却不给判定依据（面试官一问就露馅）
- ❌ 把评测集扩到 100 条、上 RAGAS、做自动打分流水线

## 卡住时的最短解法

| 卡点 | 处理 |
| --- | --- |
| 45 分钟写不完 20 条 | 降到 12 条（6/3/3），但**必须保留拒答类**，README 注明样本数 |
| 指标很难看 | 好事，照实写。难看的数据 + 归因，比漂亮数字可信得多 |
| 不确定答案对不对 | 语料是你自己写的笔记，你就是标准答案 |
| 出题卡住 | 从 `10_目标/` 里找带数字、带「为什么」的句子，改写成问题 |

> 这张表就是 [[Day7_简历与面试弹药]] 里那个可验证数字的来源。别省。

## 关联

[[Day2_手写最小RAG]] · [[Day4_单次可归因优化]] · [[交付自检脚本]] · [[简历项目描述模板]] · [[面试自检题库]]
