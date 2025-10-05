from typing import List, runtime_checkable, Protocol, Union, Sequence, Mapping
import cv2
import numpy as np
from pathlib import Path

from .config import SUPPORTED_FORMATS


def load_img(img: str | np.ndarray) -> np.ndarray:
    """
    이미지 로드
    Args:
        img(str|np.ndarray): 이미지 경로 | 이미지 numpy 배열
    """
    # img_type = "local"  # local, s3

    # 이미 np array인 경우 그냥 돌려줌
    if isinstance(img, np.ndarray):
        return img

    path = Path(img)

    image = None
    if path.is_file():
        # local file image
        if not path.exists():
            raise FileNotFoundError(f"[{img}] Image not found")
        if path.suffix.lower() not in SUPPORTED_FORMATS:
            raise ValueError(
                f"[{img}] Unsupported image format: {path.suffix}"
            )

        image = cv2.imread(img, cv2.IMREAD_COLOR)
    # TODO: 이미지가 웹 url 인 경우.
    # else:

    if image is None:
        raise ValueError(f"[{img}] Failed to load image")

    return image


def load_target_imgs(img_paths: List[str]) -> List[np.ndarray]:
    """
    target 이미지 로드

    Args:
        img_paths (List[str]): 이미지 경로를 배열로 받음
    """
    targets = []
    for path in img_paths:
        targets.append(load_img(path))

    return targets

@runtime_checkable
class OverlapRange(Protocol):
    x: int
    y: int
    w: int
    h: int

RangeInputType = Union[OverlapRange, Mapping[str, int], Sequence[int]]

def parse_range(r: RangeInputType):
    if isinstance(r, OverlapRange):
        x, y, w, h = r.x, r.y, r.w, r.h
    elif isinstance(r, Mapping):
        x, y, w, h = r["x"], r["y"], r["w"], r["h"]
    else:
        x, y, w, h = r

    return x, y, w, h

def is_overlap(range1: RangeInputType, range2: RangeInputType) -> bool:
    x1, y1, w1, h1 = parse_range(range1)
    x2, y2, w2, h2 = parse_range(range2)

    min_x_end = min(x1 + w1, x2 + w2)
    max_x_start = max(x1, x2)
    min_y_end = min(y1 + h1, y2 + h2)
    max_y_start = max(y1, y2)

    return min_x_end > max_x_start and min_y_end > max_y_start