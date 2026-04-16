import pytest

from app.tasks.document_tasks import _chunk_text


class TestDocumentAPI:
    @pytest.mark.asyncio
    async def test_list_documents_empty(self, client):
        resp = await client.get("/api/v1/documents/")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_upload_requires_file(self, client):
        resp = await client.post("/api/v1/documents/")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_get_nonexistent_document(self, client):
        resp = await client.get("/api/v1/documents/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404


class TestQuestionAPI:
    @pytest.mark.asyncio
    async def test_ask_empty_question(self, client):
        resp = await client.post(
            "/api/v1/questions/",
            json={"document_id": "00000000-0000-0000-0000-000000000000", "question": ""},
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_ask_invalid_doc_id(self, client):
        resp = await client.post(
            "/api/v1/questions/",
            json={"document_id": "not-a-uuid", "question": "test"},
        )
        assert resp.status_code == 400
