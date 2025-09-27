from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class TargetImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    url_id: Optional[str] = None
    file_path: str
    file_size: int
    mime_type: str
    is_active: bool
    tags: Optional[List[str]] = None
    created_at: datetime
    file_path_type: str = "local"


class TargetImageListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: List[TargetImageResponse]
    page: int
    cnt: int


class ProcessedImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url_id: Optional[str] = None
    marked_file_size: int
    marked_file_mime_type: str
    marked_file_type: str = "local"
    sliced_file_size: Optional[int] = None
    sliced_file_mime_type: Optional[str] = None
    sliced_file_type: str = "local"
    created_at: datetime

class ProcessedImageListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: List[ProcessedImageResponse]
    page: int
    cnt: int