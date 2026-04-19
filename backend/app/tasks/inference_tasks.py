import uuid

from app.tasks.celery_app import celery_app


def _reset_async_singletons():
    import app.db.mongo as mongo_mod
    mongo_mod._mongo_client = None
    mongo_mod._mongo_db = None

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    import app.db.postgres as postgres_mod
    postgres_mod.engine = create_async_engine(
        postgres_mod.settings.postgres_url, echo=False, pool_size=20, max_overflow=10
    )
    postgres_mod.async_session = async_sessionmaker(
        postgres_mod.engine, class_=AsyncSession, expire_on_commit=False
    )


@celery_app.task(bind=True, max_retries=3)
def answer_question_task(self, question_id: str, document_id: str, question: str):
    import asyncio

    _reset_async_singletons()

    from app.db.postgres import async_session
    from app.services.rag_service import RAGService

    async def _answer():
        async with async_session() as db:
            svc = RAGService(db)
            result = await svc.answer(question_id, document_id, question)

        async with async_session() as db:
            from app.services.document_service import QuestionService
            qsvc = QuestionService(db)
            await qsvc.update_answer(
                uuid.UUID(question_id),
                result["answer"],
                result["sources"],
                result["status"],
            )

        return result

    try:
        return asyncio.run(_answer())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)
