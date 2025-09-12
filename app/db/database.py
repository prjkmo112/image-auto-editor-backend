import os
from urllib.parse import urlparse
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

parsed_url = urlparse(os.getenv("DATABASE_URL"))
# db_url = f"postgresql://{parsed_url.username}:{parsed_url.password}@{parsed_url.hostname}:{parsed_url.port}/{parsed_url.path[1:]}"
db_url = os.getenv("DATABASE_URL")

engine = create_async_engine(
    db_url, future=True, pool_size=10, pool_recycle=3600
)
session = async_sessionmaker(
    bind=engine, autocommit=False, autoflush=False, expire_on_commit=False
)

Base = declarative_base()


async def get_db():
    async with session() as sess:
        try:
            yield sess
        except Exception:
            await sess.rollback()
            raise
        finally:
            await sess.close()


async def close_db():
    await engine.dispose()
