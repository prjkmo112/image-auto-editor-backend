import hashlib
import os
import uuid
from pathlib import Path
from typing import List

import aiofiles
from fastapi import APIRouter, UploadFile, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.api_valid import valid_image_depends
from app.db.database import get_db

from modules.ImageAutoEditor import mark_and_slice_image, MatcherBuilder
from app.db.models import SourceImages, TargetImages

router = APIRouter()

@router.post("/remove")
async def proc_image(tags: List[str],
                     target_filter_tags: List[str],
                     target_filter_names: List[str],
                     file: UploadFile = Depends(valid_image_depends),
                     db: AsyncSession = Depends(get_db),):
    """
    image proc
    """
    # orgfile - make upload dir
    upload_dir = Path(os.getenv("SAVED_IMG_DIR")) / "oimg"
    upload_dir.mkdir(parents=True, exist_ok=True)

    # orgfile - write
    file_ext = file.filename.split(".")[-1].lower()
    org_filename = f"{uuid.uuid4()}.{file_ext}"
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
        file_path=str(org_file_path),
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
             .where(TargetImages.tags.any(tags)))
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

    return {"status": "ok"}
