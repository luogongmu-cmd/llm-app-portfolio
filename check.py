# check.py — 项目交付自检（标准库实现，无第三方依赖）
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
results = []


def add(name, passed, hint=""):
    results.append((name, bool(passed), hint))


# 1. README 结构与首屏
readme = ROOT / "README.md"
text = readme.read_text(encoding="utf-8") if readme.exists() else ""
add("README.md 存在", bool(text))
for sec in ["快速开始", "架构", "评测", "已知限制"]:
    add(f"README 含「{sec}」章节", sec in text)
add("README 有 Demo 链接", "http" in text)

# 2. 密钥与忽略规则
gi_path = ROOT / ".gitignore"
gi = gi_path.read_text(encoding="utf-8") if gi_path.exists() else ""
add(".gitignore 忽略 .env", ".env" in gi)
add(".env.example 存在", (ROOT / ".env.example").exists())

# 3. 禁用框架（Day2 起硬要求；第 1–2 周引入 LangGraph 后改为只检查手写版本仍在）
banned = re.compile(r"^\s*(?:from|import)\s+(langchain|langgraph|llama_index)", re.M)
handwritten = ROOT / "agent_loop.py"
hw_text = handwritten.read_text(encoding="utf-8", errors="ignore") if handwritten.exists() else ""
add("手写循环仍在且未引入框架", bool(hw_text) and not banned.search(hw_text))
add("LangGraph 版存在（agent_graph.py）", (ROOT / "agent_graph.py").exists())

# 4. 评测集配比
cases = ROOT / "eval" / "cases.jsonl"
if cases.exists():
    rows = [json.loads(x) for x in cases.read_text(encoding="utf-8").splitlines() if x.strip()]
    kinds = [r.get("type", "") for r in rows]
    add("评测集 ≥ 12 条", len(rows) >= 12, f"当前 {len(rows)} 条")
    add("含拒答类样本 ≥ 3", kinds.count("no_answer") >= 3, f"当前 {kinds.count('no_answer')} 条")
    add("含跨段综合样本 ≥ 3", kinds.count("multi_chunk") >= 3, f"当前 {kinds.count('multi_chunk')} 条")
    add("每条都有 expect 字段", all(r.get("expect") for r in rows))
else:
    add("eval/cases.jsonl 存在", False, "Day3 产出")

# 5. 前后两次评测结果（CI 里 runs/ 被 gitignore，跳过）
if os.getenv("CI"):
    add("评测结果检查（CI 环境跳过）", True)
else:
    runs_dir = ROOT / "eval" / "runs"
    runs = sorted(runs_dir.glob("*.json")) if runs_dir.exists() else []
    add("有 ≥2 次评测结果（改动前/后）", len(runs) >= 2, f"当前 {len(runs)} 个")

# 6. git 状态
try:
    def git(*args):
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                              text=True, encoding="utf-8", errors="ignore").stdout.strip()

    tracked = set(git("ls-files").splitlines())
    add(".env 未被 git 跟踪", ".env" not in tracked)
    count = git("rev-list", "--count", "HEAD") or "0"
    add("commit 数 ≥ 7", int(count) >= 7, f"当前 {count} 个")
    add("工作区干净（已提交）", git("status", "--porcelain") == "")
except Exception as exc:  # git 未安装或不是仓库
    add("git 检查", False, str(exc))

# 7. 输出
for name, passed, hint in results:
    mark = "PASS" if passed else "FAIL"
    tail = f"  <- {hint}" if (hint and not passed) else ""
    print(f"[{mark}] {name}{tail}")

failed = sum(1 for _, p, _ in results if not p)
print(f"\n{len(results) - failed}/{len(results)} 通过")
sys.exit(1 if failed else 0)
