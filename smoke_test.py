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