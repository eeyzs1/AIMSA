import logging

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings

logger = logging.getLogger("aimsa")

_chroma_client = None


def get_chroma():
    global _chroma_client
    if _chroma_client is None:
        if settings.CHROMA_MODE == "ephemeral":
            _chroma_client = chromadb.EphemeralClient(
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            logger.info("ChromaDB running in ephemeral (in-memory) mode")
        else:
            _chroma_client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIR,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            logger.info(f"ChromaDB running in persistent mode at {settings.CHROMA_PERSIST_DIR}")
    return _chroma_client


def get_or_create_collection(name: str = "documents"):
    client = get_chroma()
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )
