import json
import os
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
os.chdir(BASE)                      # 让 query.py 的 .chroma 指向项目根，而不是 eval/
sys.path.insert(0, str(BASE))
from query import answer, search  # noqa: E402  Day2 的实现

rows = [json.loads(x) for x in
        (BASE / "eval/cases.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]

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
(BASE / "eval/runs").mkdir(parents=True, exist_ok=True)
out = BASE / "eval/runs/after.json"   # Day4 改成 after.json 再跑一次
out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({k: v for k, v in summary.items() if k != "detail"},
                 ensure_ascii=False, indent=2))