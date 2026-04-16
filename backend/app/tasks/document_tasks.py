import re
import uuid

from app.db.vector import get_or_create_collection
from app.tasks.celery_app import celery_app
from app.config import settings

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


def _read_file(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _read_pdf(file_path: str) -> str:
    try:
        import fitz
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except ImportError:
        return _read_file(file_path)


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    paragraphs = re.split(r"\n\s*\n", text)
    chunks = []
    current = ""
    for para in paragraphs:
        while len(para) > chunk_size:
            if current.strip():
                chunks.append(current.strip())
            chunks.append(para[:chunk_size].strip())
            para = para[chunk_size - overlap:]
            current = ""
        if len(current) + len(para) > chunk_size and current:
            chunks.append(current.strip())
            current = current[-overlap:] + "\n" + para
        else:
            current += "\n" + para if current else para
    if current.strip():
        chunks.append(current.strip())
    return chunks


@celery_app.task(bind=True, max_retries=3)
def process_document_task(self, document_id: str, file_path: str):
    from app.db.postgres import async_session
    from app.services.document_service import DocumentService
    import asyncio

    async def _process():
        if file_path.lower().endswith(".pdf"):
            text = _read_pdf(file_path)
        else:
            text = _read_file(file_path)

        if not text.strip():
            async with async_session() as db:
                svc = DocumentService(db)
                await svc.update_status(uuid.UUID(document_id), "failed")
            return {"status": "failed", "reason": "empty document"}

        chunks = _chunk_text(text)
        collection = get_or_create_collection()

        ids = []
        documents = []
        metadatas = []
        for i, chunk in enumerate(chunks):
            chunk_id = f"{document_id}_chunk_{i}"
            ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append({"document_id": document_id, "chunk_index": i})

        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

        async with async_session() as db:
            svc = DocumentService(db)
            await svc.update_status(uuid.UUID(document_id), "ready", chunk_count=len(chunks))

        return {"status": "ready", "chunk_count": len(chunks)}

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_process())
        finally:
            loop.close()
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)
