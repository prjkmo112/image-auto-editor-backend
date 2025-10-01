from typing import get_args, List

import cv2
import numpy as np
import logging

from .base import BaseMatcher
from modules.ImageAutoEditor.common.types import HashMethod, MatchResult

logger = logging.getLogger(__name__)


class HashMatcher(BaseMatcher):
    def __init__(
        self,
        threshold: float,
        method: HashMethod,
        hash_size: int = 8,
        stride_ratio: float = 0.25,
    ):
        super().__init__(threshold)

        self.name = f"Hash - {method}"
        self.hash_size = hash_size
        self.stride_ratio = stride_ratio
        self.method = method
        if method not in get_args(HashMethod):
            raise ValueError("Invalid template matching method")

    def _match_impl(self, org: np.ndarray, targ: np.ndarray) -> List[MatchResult]:
        template_hash = self.__calculate_hash(targ)
        matches = self.__sliding_window_match(
            org, template_hash, targ.shape[:2]
        )
        return matches

    def __calculate_hash(self, image: np.ndarray) -> np.ndarray:
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        if self.method == "AHASH":
            return self.__ahash(image)
        elif self.method == "PHASH":
            return self.__phash(image)
        elif self.method == "DHASH":
            return self.__dhash(image)
        else:
            raise ValueError("Unknown hash method")

    def __ahash(self, image: np.ndarray) -> np.ndarray:
        """
        Average Hash
        """
        image = cv2.resize(
            image,
            (self.hash_size, self.hash_size),
            interpolation=cv2.INTER_AREA,
        )
        avg = np.mean(image)
        return (image > avg).astype(np.uint8).flatten()

    def __phash(self, image: np.ndarray) -> np.ndarray:
        """
        Perceptual Hash
        """
        img_size = self.hash_size * 4
        image = cv2.resize(
            image, (img_size, img_size), interpolation=cv2.INTER_AREA
        )

        dct = cv2.dct(np.float32(image))
        dct_low = dct[1 : self.hash_size + 1, 1 : self.hash_size + 1]

        avg = np.mean(dct_low)
        return (dct_low > avg).astype(np.uint8).flatten()

    def __dhash(self, image: np.ndarray) -> np.ndarray:
        """
        Difference Hash
        """
        image = cv2.resize(
            image,
            (self.hash_size + 1, self.hash_size),
            interpolation=cv2.INTER_AREA,
        )
        diff = image[:, 1:] > image[:, :-1]
        return diff.astype(np.uint8).flatten()

    def __sliding_window_match(
        self,
        original_img: np.ndarray,
        template_hash: np.ndarray,
        template_shape: tuple,
    ) -> List[MatchResult]:
        """슬라이딩 윈도우로 해시 매칭"""
        matches = []
        temp_h, temp_w = template_shape
        orig_h, orig_w = original_img.shape[:2]

        # stride
        stride_x = max(1, int(temp_w * self.stride_ratio))
        stride_y = max(1, int(temp_h * self.stride_ratio))

        total_windows = ((orig_h - temp_h) // stride_y + 1) * (
            (orig_w - temp_w) // stride_x + 1
        )
        logger.debug(
            f"[{self.name}] {total_windows}개 윈도우 검사 (간격: {stride_x}x{stride_y})"
        )

        for y in range(0, orig_h - temp_h + 1, stride_y):
            for x in range(0, orig_w - temp_w + 1, stride_x):
                # 윈도우 추출
                window = original_img[y : y + temp_h, x : x + temp_w]

                # 윈도우 해시 계산
                window_hash = self.__calculate_hash(window)

                # 유사도 계산
                similarity = self._calculate_similarity(
                    template_hash, window_hash
                )

                # 임계값 확인
                if similarity >= self.threshold:
                    match = MatchResult(
                        x=x,
                        y=y,
                        w=temp_w,
                        h=temp_h,
                        similarity=similarity,
                        method=self.method,
                    )
                    matches.append(match)

        return matches

    def _calculate_similarity(
        self, hash1: np.ndarray, hash2: np.ndarray
    ) -> float:
        if len(hash1) != len(hash2):
            return 0.0

        # 해밍 거리 계산
        hamming_distance = np.sum(hash1 != hash2)

        # 유사도로 변환
        similarity = 1.0 - (hamming_distance / len(hash1))
        return max(0.0, min(1.0, similarity))
