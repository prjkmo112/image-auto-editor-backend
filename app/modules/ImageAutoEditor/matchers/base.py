import logging
from abc import ABC, abstractmethod
from typing import List
from functools import wraps

import numpy as np

from app.modules.ImageAutoEditor.common.types import MatchResult

logger = logging.getLogger(__name__)


def preproc_match(func):
    @wraps(func)
    def wrapper(self, org: np.ndarray, targ: np.ndarray):
        # validation
        if org is None or targ is None:
            logger.debug("image is None")
            return []

        orig_h, orig_w = org.shape[:2]
        targ_h, targ_w = targ.shape[:2]

        if targ_w > orig_w or targ_h > orig_h:
            logger.debug(
                f"Target Image Size Error\n    Target Image: {targ_w}x{targ_h})\nOriginal Image({orig_w}x{orig_h}"
            )
            return []

        if targ_w < 5 or targ_h < 5:
            logger.debug(f"Target Image is too small: {targ_w}x{targ_h}")
            return []

        try:
            # matching
            matches = func(self, org, targ)

            # log
            self._log_result(matches)

            return matches
        except Exception as e:
            logger.error(f"Matching Error: {e}")
            return []

    return wrapper


class BaseMatcher(ABC):
    name: str

    def __init__(self, threshold: float):
        self.threshold = threshold

    @preproc_match
    def match(self, org: np.ndarray, targ: np.ndarray) -> list[MatchResult]:
        """
        Args:
            org (np.ndarray): 원본 이미지
            targ (np.ndarray): 타겟 이미지
        """
        return self._match_impl(org, targ)

    @abstractmethod
    def _match_impl(self, org: np.ndarray, targ: np.ndarray) -> list[MatchResult]:
        """
        Args:
            org (np.ndarray): 원본 이미지
            targ (np.ndarray): 타겟 이미지
        """
        raise NotImplementedError

    def _log_result(self, matches: List[MatchResult]) -> None:
        logger.debug(f"[{self.name}] {len(matches)}개 매칭 발견")
        for i, match in enumerate(matches[:3]):  # 최대 3개만 출력
            logger.debug(
                f"  {i + 1}. ({match.x}, {match.y}) {match.w}x{match.h} "
                f"유사도: {match.similarity:.3f}"
            )
        if len(matches) > 3:
            logger.debug(f"  ... 외 {len(matches) - 3}개")
