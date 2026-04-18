import os
import uuid
from datetime import datetime

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.vector import get_or_create_collection
from app.models.document import Document, Question
from app.tasks.document_tasks import process_document_task
from app.tasks.inference_tasks import answer_question_task


class DocumentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upload(self, filename: str, content_type: str, content: bytes) -> Document:
        doc_id = uuid.uuid4()
        file_path = os.path.join(settings.UPLOAD_DIR, f"{doc_id}_{filename}")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(content)

        doc = Document(id=doc_id, filename=filename, content_type=content_type, file_path=file_path)
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)

        process_document_task.delay(str(doc.id), file_path)
        return doc

    async def get(self, doc_id: uuid.UUID) -> Document | None:
        result = await self.db.execute(select(Document).where(Document.id == doc_id))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Document]:
        result = await self.db.execute(select(Document).order_by(Document.created_at.desc()))
        return list(result.scalars().all())

    async def update_status(self, doc_id: uuid.UUID, status: str, chunk_count: int = 0):
        await self.db.execute(
            update(Document)
            .where(Document.id == doc_id)
            .values(status=status, chunk_count=chunk_count, updated_at=datetime.utcnow())
        )
        await self.db.commit()

    async def delete_document(self, doc_id: uuid.UUID) -> bool:
        doc = await self.get(doc_id)
        if not doc:
            return False

        if doc.file_path and os.path.exists(doc.file_path):
            os.remove(doc.file_path)

        try:
            collection = get_or_create_collection()
            doc_id_str = str(doc_id)
            existing = collection.get(where={"document_id": doc_id_str})
            if existing and existing["ids"]:
                collection.delete(ids=existing["ids"])
        except Exception:
            pass

        await self.db.execute(delete(Question).where(Question.document_id == doc_id))
        await self.db.delete(doc)
        await self.db.commit()
        return True


class QuestionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def ask(self, document_id: uuid.UUID, question: str) -> Question:
        q = Question(document_id=document_id, question=question)
        self.db.add(q)
        await self.db.commit()
        await self.db.refresh(q)

        answer_question_task.delay(str(q.id), str(document_id), question)
        return q

    async def get(self, question_id: uuid.UUID) -> Question | None:
        result = await self.db.execute(select(Question).where(Question.id == question_id))
        return result.scalar_one_or_none()

    async def list_by_document(self, document_id: uuid.UUID) -> list[Question]:
        result = await self.db.execute(
            select(Question).where(Question.document_id == document_id).order_by(Question.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_answer(self, question_id: uuid.UUID, answer: str, sources: str, status: str):
        await self.db.execute(
            update(Question)
            .where(Question.id == question_id)
            .values(answer=answer, sources=sources, status=status, completed_at=datetime.utcnow())
        )
        await self.db.commit()
