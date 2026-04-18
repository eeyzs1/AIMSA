from app.tasks.document_tasks import _chunk_text


class TestChunking:
    def test_short_text_single_chunk(self):
        text = "This is a short text."
        chunks = _chunk_text(text, chunk_size=500, overlap=100)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_long_text_multiple_chunks(self):
        text = "\n\n".join(["Word " * 100 for _ in range(10)])
        chunks = _chunk_text(text, chunk_size=500, overlap=100)
        assert len(chunks) > 1

    def test_empty_text_no_chunks(self):
        text = ""
        chunks = _chunk_text(text, chunk_size=500, overlap=100)
        assert len(chunks) == 0

    def test_whitespace_only_no_chunks(self):
        text = "   \n\n  \t  \n\n   "
        chunks = _chunk_text(text, chunk_size=500, overlap=100)
        assert len(chunks) == 0

    def test_overlap_preserved(self):
        text = "A" * 600
        chunks = _chunk_text(text, chunk_size=500, overlap=100)
        if len(chunks) > 1:
            assert chunks[1][:100] == "A" * 100
