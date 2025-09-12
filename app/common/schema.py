from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class TargetImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
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
