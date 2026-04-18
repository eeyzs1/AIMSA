import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    status: str
    chunk_count: int
    created_at: str

    class Config:
        from_attributes = True


@router.post("/", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")

    svc = DocumentService(db)
    doc = await svc.upload(file.filename, file.content_type or "application/octet-stream", content)
    return DocumentResponse(
        id=str(doc.id),
        filename=doc.filename,
        content_type=doc.content_type,
        status=doc.status,
        chunk_count=doc.chunk_count,
        created_at=doc.created_at.isoformat(),
    )


@router.get("/", response_model=list[DocumentResponse])
async def list_documents(db: AsyncSession = Depends(get_db)):
    svc = DocumentService(db)
    docs = await svc.list_all()
    return [
        DocumentResponse(
            id=str(d.id),
            filename=d.filename,
            content_type=d.content_type,
            status=d.status,
            chunk_count=d.chunk_count,
            created_at=d.created_at.isoformat(),
        )
        for d in docs
    ]


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    svc = DocumentService(db)
    doc = await svc.get(uuid.UUID(doc_id))
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse(
        id=str(doc.id),
        filename=doc.filename,
        content_type=doc.content_type,
        status=doc.status,
        chunk_count=doc.chunk_count,
        created_at=doc.created_at.isoformat(),
    )
