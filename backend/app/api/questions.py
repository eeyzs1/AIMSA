import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.services.document_service import QuestionService

router = APIRouter(prefix="/questions", tags=["questions"])


class AskRequest(BaseModel):
    document_id: str
    question: str


class QuestionResponse(BaseModel):
    id: str
    document_id: str
    question: str
    answer: str | None
    status: str
    created_at: str
    completed_at: str | None


@router.post("/", response_model=QuestionResponse)
async def ask_question(req: AskRequest, db: AsyncSession = Depends(get_db)):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    try:
        uuid.UUID(req.document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document_id format")

    svc = QuestionService(db)
    q = await svc.ask(uuid.UUID(req.document_id), req.question)
    return QuestionResponse(
        id=str(q.id),
        document_id=str(q.document_id),
        question=q.question,
        answer=q.answer,
        status=q.status,
        created_at=q.created_at.isoformat(),
        completed_at=q.completed_at.isoformat() if q.completed_at else None,
    )


@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(question_id: str, db: AsyncSession = Depends(get_db)):
    svc = QuestionService(db)
    q = await svc.get(uuid.UUID(question_id))
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    return QuestionResponse(
        id=str(q.id),
        document_id=str(q.document_id),
        question=q.question,
        answer=q.answer,
        status=q.status,
        created_at=q.created_at.isoformat(),
        completed_at=q.completed_at.isoformat() if q.completed_at else None,
    )


@router.get("/by-document/{doc_id}", response_model=list[QuestionResponse])
async def list_questions(doc_id: str, db: AsyncSession = Depends(get_db)):
    svc = QuestionService(db)
    questions = await svc.list_by_document(uuid.UUID(doc_id))
    return [
        QuestionResponse(
            id=str(q.id),
            document_id=str(q.document_id),
            question=q.question,
            answer=q.answer,
            status=q.status,
            created_at=q.created_at.isoformat(),
            completed_at=q.completed_at.isoformat() if q.completed_at else None,
        )
        for q in questions
    ]
