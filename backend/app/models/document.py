import enum
import uuid

from sqlalchemy import String, Text, DateTime, ForeignKey, Index, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.postgres import Base


class DocumentStatus(str, enum.Enum):
    uploaded = "uploaded"
    processing = "processing"
    ready = "ready"
    failed = "failed"


class QuestionStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_documents_status", "status"),
        Index("ix_documents_created_at", "created_at"),
        Index("ix_documents_status_created", "status", "created_at"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(default=DocumentStatus.uploaded)
    chunk_count: Mapped[int] = mapped_column(default=0)
    processing_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(DateTime, server_default="now()")
    updated_at: Mapped[str] = mapped_column(DateTime, server_default="now()")

    questions: Mapped[list["Question"]] = relationship(back_populates="document")


class Question(Base):
    __tablename__ = "questions"
    __table_args__ = (
        Index("ix_questions_document_id", "document_id"),
        Index("ix_questions_status", "status"),
        Index("ix_questions_created_at", "created_at"),
        Index("ix_questions_doc_status", "document_id", "status"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str | None] = mapped_column(Text)
    sources: Mapped[str | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(default=QuestionStatus.pending)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    token_count: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[str] = mapped_column(DateTime, server_default="now()")
    completed_at: Mapped[str | None] = mapped_column(DateTime)

    document: Mapped["Document"] = relationship(back_populates="questions")
