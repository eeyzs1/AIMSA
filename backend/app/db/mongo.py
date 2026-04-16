from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings

mongo_client = AsyncIOMotorClient(settings.mongo_url)
mongo_db = mongo_client[settings.MONGO_DB]


def get_mongo():
    return mongo_db


async def log_inference(task_id: str, data: dict):
    collection = mongo_db.inference_logs
    await collection.insert_one({"task_id": task_id, **data})


async def log_metric(service: str, metric: dict):
    collection = mongo_db.metrics
    await collection.insert_one({"service": service, **metric})
