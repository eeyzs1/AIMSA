import logging
from datetime import datetime, timedelta

import httpx
from fastapi import APIRouter
from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy import text

from app.config import settings
from app.db.postgres import engine
from app.db.vector import get_chroma

logger = logging.getLogger("aimsa")

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

mongo_client = AsyncIOMotorClient(settings.mongo_url)
mongo_db = mongo_client[settings.MONGO_DB]


async def _check_postgres() -> dict:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except Exception as e:
        logger.warning(f"PostgreSQL health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


async def _check_mongodb() -> dict:
    try:
        result = await mongo_client.admin.command("ping")
        if result.get("ok"):
            return {"status": "healthy"}
        return {"status": "unhealthy", "error": "ping returned ok=0"}
    except Exception as e:
        logger.warning(f"MongoDB health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


async def _check_redis() -> dict:
    try:
        import redis as redis_sync

        r = redis_sync.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
        r.ping()
        return {"status": "healthy"}
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


async def _check_chromadb() -> dict:
    try:
        client = get_chroma()
        client.heartbeat()
        return {"status": "healthy"}
    except Exception as e:
        logger.warning(f"ChromaDB health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


async def _check_llm_service() -> dict:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.LLM_SERVICE_URL}/health")
            resp.raise_for_status()
            return {"status": "healthy", "detail": resp.json()}
    except Exception as e:
        logger.warning(f"LLM service health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


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
    checks = {
        "postgresql": await _check_postgres(),
        "mongodb": await _check_mongodb(),
        "redis": await _check_redis(),
        "chromadb": await _check_chromadb(),
        "llm_service": await _check_llm_service(),
    }
    all_healthy = all(c["status"] == "healthy" for c in checks.values())
    overall = "healthy" if all_healthy else "degraded"
    return {
        "status": overall,
        "timestamp": datetime.utcnow().isoformat(),
        "services": checks,
    }
