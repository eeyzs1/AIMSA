import uuid

from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3)
def answer_question_task(self, question_id: str, document_id: str, question: str):
    import asyncio

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
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_answer())
        finally:
            loop.close()
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)
