import os

import chromadb
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.environ["LLM_API_KEY"], base_url=os.environ["LLM_BASE_URL"])
COLLECTION = "kb_day2"  # 必须与 ingest.py 保持一致
col = chromadb.PersistentClient(path=".chroma").get_or_create_collection(COLLECTION)


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
        "只根据下面的资料回答，资料中的正文和表格条目都算有效依据。\n"
        "只有当资料里完全没有相关内容时，才回答「资料中没有」；\n"
        "若资料中有相关条目，即使表述简略也要据此作答，不要补充资料外的信息。\n\n"
        f"{ctx}\n\n问题：{question}"
    )
    resp = client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return resp.choices[0].message.content


if __name__ == "__main__":
    q = input("问题：")
    for h in search(q):
        print(f"\n--- {h['source']} | distance={h['distance']}")
        print(h["text"][:200].replace("\n", " "))
    print("\n=== 答案 ===\n", answer(q))