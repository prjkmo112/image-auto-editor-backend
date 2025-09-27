import logging
from typing import List, Optional

import cv2
import numpy as np

from .common import types, utils
from .helper import MatcherBuilder
from .multi_process_work import find_matches_parallel

logger = logging.getLogger(__name__)


def find_matches(
    original_img: str,
    target_imgs: List[str],
    mbuilder: MatcherBuilder,
    multi_process_count: int = 1,
) -> List[types.MatchResult]:
    """
    Find matches of target_img in original_img using specified methods.
    Returns a list of MatchResult objects.

    Args:
        original_img: 원본 이미지 (경로)
        target_imgs: 타겟 이미지 (경로)
        mbuilder: Match Builder
        multi_process_count
    """
    if multi_process_count <= 1:
        return __find_matches_single(original_img, target_imgs, mbuilder)
    else:
        return find_matches_parallel(
            original_img, target_imgs, mbuilder, multi_process_count
        )


def __find_matches_single(
    original_img: str,
    target_imgs: List[str],
    mbuilder: MatcherBuilder
) -> List[types.MatchResult]:
    """Single process of find_matches"""
    original_img = utils.load_img(original_img)
    target_imgs = utils.load_target_imgs(target_imgs)

    # 모든 매칭 수행
    all_matches: List[types.MatchResult] = []

    for idx, target in enumerate(target_imgs):
        logger.debug(f"\n--- 타겟 {idx + 1} 매칭")

        try:
            matches = mbuilder.match(original_img, target)
            all_matches.extend(matches)
        except Exception as e:
            logger.error(e)

    return all_matches


def slice_image(
    original_img: str,
    target_imgs: List[str],
    mbuilder: MatcherBuilder = None,
    inpaint: bool = True,
    multi_process_count: int = 1,
) -> Optional[np.ndarray]:
    """
    원본 이미지에서 등록된 객체들을 제거

        Args:
            original_img: 원본 이미지
            target_imgs: 타겟 이미지
            mbuilder
            inpaint
            multi_process_count

        Returns:
            처리된 이미지
    """
    matches = find_matches(
        original_img, target_imgs, mbuilder, multi_process_count
    )

    original_img = utils.load_img(original_img)

    if len(matches) == 0:
        logger.error("No match")
        return None

    # mask 생성
    mask = np.zeros(original_img.shape[:2], dtype=np.uint8)
    for x, y, w, h, *_ in matches:
        mask[y : y + h, x : x + w] = 255

    if inpaint:
        result_image = cv2.inpaint(original_img, mask, 3, cv2.INPAINT_TELEA)
    else:
        result_image = original_img.copy()
        result_image[mask == 255] = (255, 255, 255)

    return result_image

def mark_image(
    original_img: str,
    target_imgs: List[str],
    mbuilder: MatcherBuilder = None,
    multi_process_count: int = 1,
) -> Optional[np.ndarray]:
    """
    해시 유사도로 찾은 영역들을 빨간색 사각형으로 표시

    Args:
        original_img: 원본 이미지 경로
        target_imgs
        mbuilder
        multi_process_count

    Returns:
        표시된 이미지
    """
    matches = find_matches(
        original_img, target_imgs, mbuilder, multi_process_count
    )

    original_img = utils.load_img(original_img)

    if len(matches) == 0:
        logger.error("No match")
        return None

    # 결과 이미지 복사본 생성
    result_image = original_img.copy()

    # 매칭된 영역들에 빨간색 사각형 그리기
    logger.debug(f"\n\n\n✅ Found {len(matches)} matching")
    for i, (x, y, w, h, similarity, method, *_) in enumerate(matches):
        # 빨간색 사각형 그리기
        cv2.rectangle(result_image, (x, y), (x + w, y + h), (0, 0, 255), 3)

        # 유사도 text 추가
        text = f"{similarity:.3f} - {method}"
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]

        # text 배경 - 가독성이 너무 떨어짐
        cv2.rectangle(
            result_image,
            (x, y - text_size[1] - 10),
            (x + text_size[0] + 10, y),
            (0, 0, 255),
            -1,
        )

        # 유사도 text (흰색)
        cv2.putText(
            result_image,
            text,
            (x + 5, y - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )

        logger.debug(
            f"  영역 {i + 1}: ({x}, {y}, {w}, {h}) 유사도: {similarity:.4f}"
        )

    return result_image

def mark_and_slice_image(
    original_img: str,
    target_imgs: List[str],
    mbuilder: MatcherBuilder = None,
    inpaint: bool = True,
    multi_process_count: int = 1,
):
    """mark + slice"""
    matches = find_matches(original_img, target_imgs, mbuilder, multi_process_count)

    original_img = utils.load_img(original_img)

    if len(matches) == 0:
        logger.error("No match")
        return None

    # mark - 복사본 생성
    mark_result_image = original_img.copy()

    # mark - 매칭 영역에 빨간 사각형 그리기
    logger.debug(f"\n\n✅ Found {len(matches)} matching")
    for i, (x, y, w, h, similarity, method, *_) in enumerate(matches):
        # 사격형 그리기
        cv2.rectangle(mark_result_image, (x, y), (x + w, y + h), (0, 0, 255), 3)

        # 유사도 text 추가
        text = f"{similarity:.3f} - {method}"
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]

        # text 배경 - 가독성 해결
        cv2.rectangle(mark_result_image,
                      (x, y - text_size[1] - 10),
                      (x + text_size[0] + 10, y),
                      (0, 0, 255),
                      -1)

        # 유사도 text (흰색)
        cv2.putText(mark_result_image, text, (x+5, y-5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # slice - mask 생성
    mask = np.zeros(original_img.shape[:2], dtype=np.uint8)
    for x, y, w, h, *_ in matches:
        mask[y : y + h, x : x + w] = 255

    if inpaint:
        slice_result_image = cv2.inpaint(original_img, mask, 3, cv2.INPAINT_TELEA)
    else:
        slice_result_image = original_img.copy()
        slice_result_image[mask == 255] = (255, 255, 255)

    return slice_result_image, mark_result_image