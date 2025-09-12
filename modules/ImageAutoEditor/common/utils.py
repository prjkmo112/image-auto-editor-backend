from typing import List
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
