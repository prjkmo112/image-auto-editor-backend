import hashlib
import os
import uuid
from pathlib import Path
from typing import List

import aiofiles
import cv2
from fastapi import APIRouter, UploadFile, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.depends import depends_tags
from app.common.depends.depends_image import valid_image_depends
from app.common.schema import ProcessedImageResponse, ProcessedImageListResponse
from app.db.database import get_db

from modules.ImageAutoEditor import mark_and_slice_image, MatcherBuilder
from app.db.models import SourceImages, TargetImages, ProcessedImages

router = APIRouter()

@router.post("/remove")
async def proc_image(
        tags: List[str] = Depends(depends_tags.tags_str_depends),
        file: UploadFile = Depends(valid_image_depends),
        db: AsyncSession = Depends(get_db)
):
    """
    image proc
    """
    # orgfile - make upload dir
    upload_dir = Path(os.getenv("SAVED_IMG_DIR")) / "oimg"
    upload_dir.mkdir(parents=True, exist_ok=True)

    # orgfile - write
    file_ext = file.filename.split(".")[-1].lower()
    org_fileid = uuid.uuid4()
    org_filename = f"{org_fileid}.{file_ext}"
    org_file_path = upload_dir / org_filename

    hash_sha256 = hashlib.sha256()
    async with aiofiles.open(org_file_path, "wb") as out:
        while True:
            chunk = await file.read(1024**2)
            if not chunk:
                break

            hash_sha256.update(chunk)
            await out.write(chunk)

    # orgfile - db save
    db_img = SourceImages(
        file_path=str(org_file_path.absolute()),
        file_path_type="local",
        file_size=file.size,
        mime_type=file.content_type,
        file_hash=hash_sha256.hexdigest(),
        original_filename=file.filename,
        tags=tags,
    )

    db.add(db_img)
    await db.commit()
    await db.refresh(db_img)

    # target img - get path
    query = (select(TargetImages.file_path)
             .where(TargetImages.is_active)
             .where(TargetImages.tags.contains(tags)))
    result = await db.execute(query)
    target_imgs = result.scalars().all()

    mbuilder = MatcherBuilder() \
        .set_config("early_stop", True) \
        .set_tm_matcher(0.9, "TM_CCOEFF_NORMED") \
        .set_sift_matcher(0.9, min_match_count=1000)

    sliced, marked = mark_and_slice_image(
        original_img=str(org_file_path),
        target_imgs=list(target_imgs),
        mbuilder=mbuilder,
        inpaint=False,
        multi_process_count=os.cpu_count()
    )

    output_sliced_dir = Path(os.getenv("SAVED_IMG_DIR")) / "sliced"
    output_marked_dir = Path(os.getenv("SAVED_IMG_DIR")) / "marked"
    output_sliced_file = output_sliced_dir / org_filename
    output_marked_file = output_marked_dir / org_filename
    output_sliced_dir.mkdir(parents=True, exist_ok=True)
    output_marked_dir.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_sliced_file), sliced)
    cv2.imwrite(str(output_marked_file), marked)

    db_proc_img = ProcessedImages(
        marked_file_path=str(output_marked_file.absolute()),
        marked_file_type="local",
        marked_file_size=marked.size,
        marked_file_mime_type=file.content_type,
        sliced_file_path=str(output_sliced_file.absolute()),
        sliced_file_type="local",
        sliced_file_size=sliced.size,
        sliced_file_mime_type=file.content_type,
        file_hash=hash_sha256.hexdigest(),
        url_id=str(org_fileid),
    )

    db.add(db_proc_img)
    await db.commit()
    await db.refresh(db_proc_img)

    return {"status": "ok"}

@router.get("/list", response_model=ProcessedImageListResponse)
async def get_proc_image_list(
        page: int = 1,
        size: int = 10,
        db: AsyncSession = Depends(get_db),
):
    query = select(ProcessedImages)

    query = (
        query.order_by(ProcessedImages.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
    )
    result = await db.execute(query)
    items_iter = result.scalars()

    items = [ ProcessedImageResponse.model_validate(item) for item in items_iter ]

    return ProcessedImageListResponse(items=items, cnt=len(items), page=page)