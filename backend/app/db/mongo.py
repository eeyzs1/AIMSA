from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings

_mongo_client = None
_mongo_db = None


def _get_mongo_client():
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = AsyncIOMotorClient(
            settings.mongo_url,
            maxPoolSize=20,
            minPoolSize=5,
            connectTimeoutMS=5000,
            serverSelectionTimeoutMS=5000,
            socketTimeoutMS=30000,
        )
    return _mongo_client


def get_mongo():
    global _mongo_db
    if _mongo_db is None:
        _mongo_db = _get_mongo_client()[settings.MONGO_DB]
    return _mongo_db


async def log_inference(task_id: str, data: dict):
    db = get_mongo()
    collection = db.inference_logs
    await collection.insert_one({"task_id": task_id, **data})


async def log_metric(service: str, metric: dict):
    db = get_mongo()
    collection = db.metrics
    await collection.insert_one({"service": service, **metric})
