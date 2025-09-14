from http.client import HTTPException
from io import BytesIO

from PIL import Image, ImageFilter
from fastapi import APIRouter
from pathlib import Path

from starlette.responses import FileResponse, StreamingResponse

router = APIRouter()

@router.get("/{image_id}")
async def get_image(
        image_id: str = Path(),
        blur: int = 0,
        width: int = 0,
        height: int = 0
):
    path = Path(f"./images/eimg/{image_id}.png")
    if not path.exists():
        raise HTTPException(404)

    if blur == 0 and width == 0 and height == 0:
        return FileResponse(path, media_type="image/png")

    img = Image.open(path)
    if blur > 0:
        img = img.filter(ImageFilter.GaussianBlur(blur))
    if width > 0 and height > 0:
        img = img.resize((width, height))

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")