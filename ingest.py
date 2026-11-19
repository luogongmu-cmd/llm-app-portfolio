import glob
import os

import chromadb
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
CHUNK, OVERLAP = 500, 50           # Day4 实验结论：100 更差，已回退到 50
# chromadb 1.x 要求集合名 3-512 字符、仅 [a-zA-Z0-9._-]；
# 骨架里的 "kb" 只有 2 字符，会抛 InvalidArgumentError
COLLECTION = "kb_day2"

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
        # 跳过切分产生的碎片（如单独的 "]"），它们会污染检索
        if len(piece.strip()) < 50:
            continue
        # 评测样例不能进检索库，否则模型会直接复述 cases.jsonl（测试集泄漏）
        if any(m in piece for m in ('"id":"q', '"expect"', '"multi_chunk"')):
            continue
        emb = client.embeddings.create(
            # 文件名注入 embedding：让「Day5」这类编号参与语义匹配（breadcrumb 思路）
            model=os.environ["EMBED_MODEL"], input=f"{name}\n{piece}"
        ).data[0].embedding
        col.add(
            ids=[f"{name}-{idx}"],
            documents=[piece],
            embeddings=[emb],
            # source 必须存：Day3 算命中率、Day4 做过滤都靠它
            metadatas=[{"source": name, "idx": idx}],
        )

print("indexed chunks:", col.count())