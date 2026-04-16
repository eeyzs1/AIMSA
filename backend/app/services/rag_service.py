import json
import time

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.mongo import log_inference, log_metric
from app.db.vector import get_or_create_collection
from app.models.document import Question


class RAGService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def retrieve(self, document_id: str, query: str, top_k: int = 3) -> list[dict]:
        collection = get_or_create_collection()
        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            where={"document_id": document_id},
        )

        chunks = []
        if results and results["documents"]:
            for doc, meta, dist in zip(
                results["documents"][0], results["metadatas"][0], results["distances"][0]
            ):
                chunks.append({"text": doc, "metadata": meta, "distance": dist})
        return chunks

    async def generate(self, question: str, context_chunks: list[dict]) -> str:
        context = "\n---\n".join(chunk["text"] for chunk in context_chunks)
        prompt = (
            '基于以下文档内容回答问题。如果文档中没有相关信息，请回答"根据提供的文档内容，无法回答该问题"。\n\n'
            f'文档内容：\n{context}\n\n'
            f'问题：{question}\n\n'
            '回答：'
        )

        start = time.time()
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{settings.LLM_SERVICE_URL}/generate",
                json={"prompt": prompt, "max_tokens": 512},
            )
            resp.raise_for_status()
            result = resp.json()
        latency = time.time() - start

        await log_metric("llm_inference", {"latency": latency, "tokens": result.get("tokens", 0)})

        return result["text"]

    async def answer(self, question_id: str, document_id: str, question: str) -> dict:
        start = time.time()
        chunks = []
        try:
            chunks = await self.retrieve(document_id, question)
            answer = await self.generate(question, chunks)
            sources = json.dumps(
                [{"chunk_index": c["metadata"].get("chunk_index", 0), "distance": c["distance"]} for c in chunks],
                ensure_ascii=False,
            )
            status = "completed"
        except Exception as e:
            answer = f"处理失败: {str(e)}"
            sources = "[]"
            status = "failed"

        total_latency = time.time() - start
        await log_inference(question_id, {"latency": total_latency, "status": status, "chunk_count": len(chunks)})

        return {"answer": answer, "sources": sources, "status": status}
