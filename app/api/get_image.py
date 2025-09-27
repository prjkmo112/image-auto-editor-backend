import os
from http.client import HTTPException
from io import BytesIO

from PIL import Image, ImageFilter
from fastapi import APIRouter, Path as PathParam
from fastapi.responses import FileResponse, StreamingResponse
from pathlib import Path

router = APIRouter()

def proc_image(
        file_path: Path,
        blur: int = 0,
        width: int = 0,
        height: int = 0
):
    if not file_path.exists():
        raise HTTPException(404)

    if blur == 0 and width == 0 and height == 0:
        return FileResponse(file_path, media_type="image/png")

    img = Image.open(file_path)
    if blur > 0:
        img = img.filter(ImageFilter.GaussianBlur(blur))
    if width > 0 and height > 0:
        img = img.resize((width, height))

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")

@router.get("/target/{image_id}")
async def get_image(
        image_id: str = PathParam(),
        blur: int = 0,
        width: int = 0,
        height: int = 0
):
    path = Path(os.getenv("SAVED_IMG_DIR")) / "eimg" / f"{image_id}.png"
    return proc_image(path, blur, width, height)

@router.get("/marked/{image_id}")
async def get_marked_image(
        image_id: str = PathParam(),
        blur: int = 0,
        width: int = 0,
        height: int = 0
):
    path = Path(os.getenv("SAVED_IMG_DIR")) / "marked" / f"{image_id}.jpg"
    return proc_image(path, blur, width, height)

@router.get("/sliced/{image_id}")
async def get_sliced_image(
        image_id: str = PathParam(),
        blur: int = 0,
        width: int = 0,
        height: int = 0
):
    path = Path(os.getenv("SAVED_IMG_DIR")) / "sliced" / f"{image_id}.jpg"
    return proc_image(path, blur, width, height)