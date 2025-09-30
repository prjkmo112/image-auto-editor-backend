from typing import get_args
import cv2
import numpy as np

from .base import BaseMatcher
from modules.ImageAutoEditor.common.types import TemplateMethod, MatchResult
from ..common import utils
from ..common.config import MATCHERS_CONFIG

class TemplateMatcher(BaseMatcher):
    cv_method: int

    def __init__(self, threshold: float, method: TemplateMethod):
        super().__init__(threshold)

        self.name = f"Template - {method}"
        self.method = method
        if method not in get_args(TemplateMethod):
            raise ValueError("Invalid template matching method")

        self.cv_method = getattr(cv2, method, None)
        self.is_inverse = True if self.method == "TM_SQDIFF_NORMED" else False

    def _match_impl(self, org: np.ndarray, targ: np.ndarray) -> list[MatchResult]:
        all_config = { **MATCHERS_CONFIG }

        result = cv2.matchTemplate(org, targ, getattr(cv2, self.method))

        if self.is_inverse:
            threshold = 1 - self.threshold
            locations = np.where(result <= threshold)
        else:
            locations = np.where(result >= self.threshold)

        matches: list[MatchResult] = []
        best_matches: list[MatchResult] = []
        targ_h, targ_w = targ.shape[:2]

        for y, x in zip(locations[0], locations[1]):  # BGR -> y,x 식으로 되어있음
            similarity = float(result[y, x])
            if self.is_inverse:
                similarity = 1 - similarity

            match = MatchResult(
                x=int(x),
                y=int(y),
                w=targ_w,
                h=targ_h,
                similarity=similarity,
                method=self.method,
            )

            if not all_config.get("except_overlap"):
                matches.append(match)
            else:
                overlapped = [
                    i
                    for i, best_m in enumerate(best_matches)
                    if utils.is_overlap(best_m, match)
                ]

                if not overlapped:
                    best_matches.append(match)
                else:
                    best_idx = max(overlapped, key=lambda i: best_matches[i].similarity)
                    if match.similarity > best_matches[best_idx].similarity:
                        # match 가 더 높다면, 겹치는 것들 전부 제거하고 match를 추가함
                        for i in overlapped:
                            best_matches[i] = match

        if all_config.get("except_overlap"):
            matches = best_matches

        return matches
