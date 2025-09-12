from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from app.common import utils

utils.load_all_config()

import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.common import utils

from app.api import target_images, proc_image
from redis import asyncio as aioredis


pyproj = utils.get_pyproject()

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log", mode="a", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

# FastAPI Cache 로거 설정
logging.getLogger('fastapi_cache').setLevel(logging.DEBUG)
logging.getLogger('fastapi_cache.decorator').setLevel(logging.DEBUG)

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    redisdb = aioredis.from_url("redis://localhost:6379/0")
    FastAPICache.init(RedisBackend(redisdb), prefix="fastapi-cache")
    yield

app = FastAPI(
    title="Image Auto Editor API",
    description="이미지 자동 편집을 위한 REST API 서비스",
    version=pyproj["project"]["version"],
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(target_images.router, prefix="/api/target-images", tags=["target-images"])
app.include_router(proc_image.router, prefix="/api/proc-images", tags=["proc-image"])

@app.get("/")
async def root():
    return {
        "message": "Image Auto Editor API",
        "version": pyproj["project"]["version"],
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
