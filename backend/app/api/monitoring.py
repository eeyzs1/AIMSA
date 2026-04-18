from datetime import datetime, timedelta

from fastapi import APIRouter
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

mongo_client = AsyncIOMotorClient(settings.mongo_url)
mongo_db = mongo_client[settings.MONGO_DB]


@router.get("/stats")
async def get_stats():
    inference_logs = mongo_db.inference_logs
    metrics = mongo_db.metrics

    one_hour_ago = datetime.utcnow() - timedelta(hours=1)

    recent_inferences = await inference_logs.count_documents({"_id": {"$gte": one_hour_ago}})
    total_inferences = await inference_logs.count_documents({})

    latency_pipeline = [
        {"$match": {"latency": {"$exists": True}}},
        {"$group": {"_id": None, "avg_latency": {"$avg": "$latency"}, "max_latency": {"$max": "$latency"}}},
    ]
    latency_result = await inference_logs.aggregate(latency_pipeline).to_list(length=1)

    failure_count = await inference_logs.count_documents({"status": "failed"})

    metrics_pipeline = [
        {
            "$group": {
                "_id": "$service",
                "count": {"$sum": 1},
                "avg_latency": {"$avg": "$latency"},
                "total_tokens": {"$sum": "$tokens"},
            },
        },
    ]
    metrics_result = await metrics.aggregate(metrics_pipeline).to_list(length=100)

    services = {}
    for r in metrics_result:
        services[r["_id"]] = {
            "count": r["count"],
            "avg_latency": r.get("avg_latency", 0),
            "total_tokens": r.get("total_tokens", 0),
        }

    return {
        "total_inferences": total_inferences,
        "recent_inferences_1h": recent_inferences,
        "failure_count": failure_count,
        "avg_latency": latency_result[0]["avg_latency"] if latency_result else 0,
        "max_latency": latency_result[0]["max_latency"] if latency_result else 0,
        "services": services,
    }


@router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
