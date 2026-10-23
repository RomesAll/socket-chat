from fastapi import APIRouter, Request


router = APIRouter(tags=["health"])


@router.get("/health")
async def health(request: Request):
    postgres_ok = await request.app.state.postgres.ping()
    redis_ok = await request.app.state.redis.ping()
    mongo_ok = await request.app.state.mongo.ping()

    return {
        "postgres": "ok" if postgres_ok else "fail",
        "redis": "ok" if redis_ok else "fail",
        "mongo": "ok" if mongo_ok else "fail",
    }