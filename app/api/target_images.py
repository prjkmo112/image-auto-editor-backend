from typing import List
import os
from pathlib import Path
import uuid
import hashlib

import aiofiles
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from fastapi_cache.decorator import cache
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.depends import depends_image, depends_tags
from app.common.schema import TargetImageListResponse, TargetImageResponse
from app.db.database import get_db
from app.db.models import TargetImages

router = APIRouter()


@router.post("/register")
async def create_target_image(
    name: str,
    tags: List[str] = Depends(depends_tags.tags_str_depends),
    is_active: bool = True,
    file: UploadFile = Depends(depends_image.valid_image_depends),
    db: AsyncSession = Depends(get_db),
):
    """
    제거 대상 이미지 등록
    """
    try:
        # make upload dir
        upload_dir = Path(os.getenv("SAVED_IMG_DIR", "/tmp/saved_img")) / "eimg"
        upload_dir.mkdir(parents=True, exist_ok=True)

        # upload file
        file_ext = file.filename.split(".")[-1].lower()
        fileid = uuid.uuid4()
        filename = f"{fileid}.{file_ext}"
        file_path = upload_dir / filename

        hash_sha256 = hashlib.sha256()
        async with aiofiles.open(file_path, "wb") as out:
            while True:
                chunk = await file.read(1024**2)  # 1MB
                if not chunk:
                    break

                hash_sha256.update(chunk)
                await out.write(chunk)

        db_img = TargetImages(
            name=name,
            tags=tags,
            file_path=str(file_path.absolute()),
            file_path_type="local",
            file_size=file.size,
            mime_type=file.content_type,
            file_hash=hash_sha256.hexdigest(),
            is_active=is_active,
            url_id=str(fileid),
        )

        db.add(db_img)
        await db.commit()
        await db.refresh(db_img)
    except Exception as e:
        await db.rollback()
        print(e)
        raise HTTPException(status_code=500, detail="File upload failed.")

async def key_builder(fn, namespace, **kwargs):
    import logging
    from fastapi_cache import FastAPICache
    
    key = "test"
    prefix = FastAPICache.get_prefix()
    final_key = f"{prefix}:{namespace}:{key}" if namespace else f"{prefix}:{key}"
    
    logging.info(f"Cache key_builder - Function: {fn.__name__}")
    logging.info(f"Cache key_builder - Namespace: {namespace}")
    logging.info(f"Cache key_builder - Prefix from FastAPICache: {prefix}")
    logging.info(f"Cache key_builder - Generated key: {key}")
    logging.info(f"Cache key_builder - Expected final key: {final_key}")
    
    return key

@router.get("/list", response_model=TargetImageListResponse)
# @cache(expire=20)
async def get_target_images_list(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(10, ge=1, le=100, description="페이지 크기"),
    active_only: bool = Query(False, description="활성 이미지만 조회"),
    db: AsyncSession = Depends(get_db),
) -> TargetImageListResponse:
    """목록 조회"""
    query = select(TargetImages)

    if active_only:
        query = query.where(TargetImages.is_active)

    query = (
        query.order_by(TargetImages.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
    )
    result = await db.execute(query)
    items_iter = result.scalars()

    items = [TargetImageResponse.model_validate(item) for item in items_iter]

    return TargetImageListResponse(items=items, cnt=len(items), page=page)


# @router.delete("/{image_id}")
# async def delete_target_image(
#         image_id: str = Path(),
#         image: TargetImageResponse,
#         db: AsyncSession = Depends(get_db)
# ):
#     """이미지 삭제"""
#     try:
#         # 파일 삭제
#         if os.path.exists(image.file_path):
#             try:
#                 os.remove(image.file_path)
#             except OSError as e:
#                 # TODO: Logging Important Error
#                 print(e)
#
#         # DB row 삭제
#         query = delete(TargetImages).where(TargetImages.id == image.id)
#         await db.execute(query)
#         await db.commit()
#         return True
#     except:
#         await db.rollback()
#         return False
#
#
# @router.put("/{image_id}")
# async def update_target_image(
#     image_id: str = Path(),
#     image: TargetImageResponse,
#     name: Optional[str] = Form(None, description="name"),
#     tags: Optional[List[str]] = Form(None, description="tag"),
#     is_active: Optional[bool] = Form(None, description="status"),
#     db: AsyncSession = Depends(get_db),
# ):
#     """이미지 수정"""
#     update_data = {}
#     if name is not None:
#         update_data["name"] = name
#     if tags is not None:
#         update_data["tags"] = tags
#     if is_active is not None:
#         update_data["is_active"] = is_active
#
#     if not update_data:
#         raise HTTPException(status_code=400, detail="No data to update.")
#
#     query = (
#         update(TargetImages)
#         .where(TargetImages.id == image.id)
#         .values(**update_data)
#     )
#     await db.execute(query)
#     await db.commit()
