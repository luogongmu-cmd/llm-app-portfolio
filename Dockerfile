FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# 容器里没有 .chroma，启动时先建索引（语料已随仓库提交）
CMD ["sh", "-c", "python ingest.py && uvicorn app:app --host 0.0.0.0 --port 8000"]
