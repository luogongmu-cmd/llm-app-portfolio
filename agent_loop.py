import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from tools import TOOLS, dispatch

load_dotenv()
client = OpenAI(api_key=os.environ["LLM_API_KEY"], base_url=os.environ["LLM_BASE_URL"])
MAX_ROUNDS = 3


def run(question: str) -> str:
    msgs = [
        {"role": "system", "content": (
            "回答事实性问题前必须先调用 search_kb 检索，且只调用一次；"
            "拿到检索结果后必须立即基于结果回答，不要重复检索。"
            "检索结果只要包含与问题相关的事实或数字，就必须据此回答；"
            "不要因为片段不完整或距离数值大而拒答。"
            "如果 search_kb 返回 TOOL_ERROR，必须如实说明工具失败及原因，"
            "不得用通用知识代替检索结果。"
        )},
        {"role": "user", "content": question},
    ]
    last_error = None
    for rnd in range(1, MAX_ROUNDS + 1):
        resp = client.chat.completions.create(
            model=os.environ["LLM_MODEL"], messages=msgs, tools=TOOLS
        )
        msg = resp.choices[0].message

        if not msg.tool_calls:                      # 模型认为可以直接回答
            return msg.content or "（模型未给出答案）"

        msgs.append(msg)
        for call in msg.tool_calls:
            try:
                args = json.loads(call.function.arguments or "{}")
                result = dispatch(call.function.name, args)
            except Exception as exc:
                # 关键：把「可行动的错误原因」回灌给模型，而不是抛栈或返回 null
                last_error = f"{type(exc).__name__}: {exc}"
                result = f"TOOL_ERROR: {last_error}。请修正参数，或说明无法完成。"
            msgs.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(result, ensure_ascii=False),
            })

    hint = f"最后一次工具错误：{last_error}。" if last_error else ""
    return f"已达到工具调用上限（{MAX_ROUNDS} 轮），无法继续。{hint}请把问题拆小或补充信息。"


if __name__ == "__main__":
    print(run(input("问题：")))