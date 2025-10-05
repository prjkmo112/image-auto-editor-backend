import os
import logging
from typing import List
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np

from .helper import MatcherBuilder
from .common import types, utils

logger = logging.getLogger(__name__)


def __work(
    original_img: np.ndarray, target_img: np.ndarray, builder_info
) -> List[types.MatchResult]:
    """work"""
    try:
        mbuilder = MatcherBuilder.from_specs(builder_info)
        return mbuilder.match(original_img, target_img)
    except Exception as e:
        logger.error(e)

    return []


def find_matches_parallel(
    original_img: str,
    target_imgs: List[str],
    mbuilder: MatcherBuilder,
    multi_process_count: int | None = None,
) -> List[types.MatchResult]:
    """Multi process of find_matches"""
    original_img = utils.load_img(original_img)
    target_imgs = utils.load_target_imgs(target_imgs)

    if multi_process_count is None:
        multi_process_count = os.cpu_count() or 2

    mbuilder_info = mbuilder.serialize()

    all_matches: List[types.MatchResult] = []
    with ProcessPoolExecutor(max_workers=multi_process_count) as executor:
        future = [
            executor.submit(__work, original_img, targ, mbuilder_info)
            for targ in target_imgs
        ]
        for fut in as_completed(future):
            res = fut.result()
            all_matches.extend(res)

    return all_matches
