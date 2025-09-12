from fastapi import HTTPException, UploadFile
from . import settings


def valid_image_depends(file: UploadFile):
    if file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE / (1024 * 1024):.1f}MB",
        )

    file_extension = file.filename.split(".")[-1]
    if file_extension.lower() not in settings.ALLOWED_IMG_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}",
        )

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File is not image.")

    return file
