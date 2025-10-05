import cv2
import numpy as np
import logging

from .base import BaseMatcher
from ..common.types import MatchResult


logger = logging.getLogger(__name__)


class SiftMatcher(BaseMatcher):
    def __init__(
        self, threshold: float, min_match_count: int = 10, knn_index: int = 2
    ):
        super().__init__(threshold)

        self.name = "SIFT"
        self.threshold = threshold
        self.min_match_count = min_match_count
        self.knn_index = knn_index

        self.sift = cv2.SIFT.create()
        self.bf_matcher = cv2.BFMatcher()

    def _match_impl(self, org: np.ndarray, targ: np.ndarray) -> list[MatchResult]:
        org = cv2.cvtColor(org, cv2.COLOR_BGR2GRAY)
        targ = cv2.cvtColor(targ, cv2.COLOR_BGR2GRAY)

        # https://docs.opencv.org/4.x/d1/de0/tutorial_py_feature_homography.html
        kp_org, des_org = self.sift.detectAndCompute(org, None)
        kp_targ, des_targ = self.sift.detectAndCompute(targ, None)

        logger.debug(
            f"original keypoint: {len(kp_org)}, target keypoint: {len(kp_targ)}"
        )

        # brute force
        # matches = self.bf_matcher.knnMatch(des_targ, des_org, k=2)

        # flann
        FLANN_INDEX_KDTREE = 1
        index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
        search_params = dict(checks=50)

        flann = cv2.FlannBasedMatcher(index_params, search_params)

        matches = flann.knnMatch(des_targ, des_org, k=self.knn_index)

        # lowe's ratio test
        lowes_matches = []
        for m, n in matches:
            if m.distance < self.threshold * n.distance:
                # if m.distance < 0.7 * n.distance:
                lowes_matches.append(m)

        logger.debug(f"Lowe's match: {len(lowes_matches)}")

        if len(lowes_matches) < self.min_match_count:
            return []

        src_pts = np.float32(
            [kp_targ[m.queryIdx].pt for m in lowes_matches]
        ).reshape(-1, 1, 2)
        dst_pts = np.float32(
            [kp_org[m.trainIdx].pt for m in lowes_matches]
        ).reshape(-1, 1, 2)

        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

        h, w = targ.shape
        pts = np.float32(
            [[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]
        ).reshape(-1, 1, 2)
        dst = cv2.perspectiveTransform(pts, M)

        x_axis = dst[:, 0, 0]
        y_axis = dst[:, 0, 1]

        x_min = int(np.min(x_axis))
        x_max = int(np.max(x_axis))
        y_min = int(np.min(y_axis))
        y_max = int(np.max(y_axis))
        similarity = int(mask.ravel().sum()) / len(lowes_matches)

        return [
            MatchResult(
                x=x_min,
                y=y_min,
                w=x_max - x_min,
                h=y_max - y_min,
                similarity=similarity,
                method="SIFT",
            )
        ]
